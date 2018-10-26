import requests, json, math, os, time, re
import dateutil.parser
from collections import namedtuple
from urllib.parse import urljoin
from threading import Thread, Lock
from queue import Queue
from typing import Union

def json_to_attrs(obj, json_res, types=(str, int, type(None), )):
	for key, val in json_res.items():
		if type(val) in types:
			setattr(obj, key, val if type(val) is not str else val.strip())

_napiUrl = 'https://unsplash.com/napi/'

class Unsplash:

	def __init__(self, size_to_download='regular'):
		self.images_count_lock = Lock()
		self.images_downloaded_count = 0
		self.last_search_text = None
		self.size_to_download = size_to_download
		self.urls = Queue()

	def search(self, text, per_page=30, debug=True):
		first_page = requests.get(urljoin(_napiUrl, 'search/photos?query={}&xp=&per_page={}&page=1'.format(text.replace(' ', '%20'), per_page)))
		
		if first_page.ok:
			json_res = json.loads(first_page.text)

			self.last_search_text = text
	
			self.last_search_total_photos, self.last_search_total_pages = json_res['total'], json_res['total_pages']
			if debug:
				print('There are {} photos and {} pages for searching text "{}"'.format(self.last_search_total_photos, self.last_search_total_pages, text))

	def _add_urls(self, num_pages=10):
		if self.last_search_text:
			self.urls = Queue(num_pages)

			for i in range(1, num_pages+1):
				self.urls.put(urljoin(_napiUrl, 'search/photos?query={}&xp=&per_page=30&page={}'.format(self.last_search_text.replace(' ', '%20'), i)))

	def _get_images(self, num_pages):	
		for _ in range(num_pages):
			url = self.urls.get()
			req = requests.get(url)
			json_res = json.loads(req.text)

			for res in json_res['results']:
				photo = Photo.from_json(res)
				photo.download(self.size_to_download, '{}/{}-{}'.format(self.last_search_text, res['id'], self.size_to_download))

				with self.images_count_lock:
				 	self.images_downloaded_count += 1

			self.urls.task_done()

	def download_last_search(self, num_pages=10, image_size='regular', max_num_threads=200, debug=True):
		if image_size in ('full', 'regular', 'small', 'thumb'):
			if not os.path.exists(self.last_search_text):
				os.mkdir(self.last_search_text)

			self.size_to_download = image_size

			first_thread = Thread(target=self._add_urls, args=(num_pages, ))
			first_thread.start()
			first_thread.join()

			if debug:
				st = time.time()

			left_pages = num_pages
			while left_pages > 0:
				gotten_pages = math.ceil(left_pages / max_num_threads)
				left_pages -= gotten_pages
				t = Thread(target=self._get_images, args=(gotten_pages, ))
				t.start()

			self.urls.join()	

			if debug:
				ex_time = time.time() - st
				print('Got {} images in {} seconds ({} images per second)'.format(self.images_downloaded_count, ex_time, self.images_downloaded_count/ex_time))

class Photo:
	
	def __init__(self, id, _json=None, from_user=None):
		self.id = id
		self._json = _json
		self.from_user = from_user
		self.api_url = urljoin(_napiUrl, 'photos/{}/info'.format(self.id))

		if not self._json:
			res = requests.get(self.api_url)
			self._json = json.loads(res.text)

		json_to_attrs(self, self._json)

		if 'tags' in self._json:
			self.tags = list(map(lambda t: t['title'], self._json['tags']))
		else:
			self.tags = None
		
		if 'photo_tags' in self._json:
			self.photo_tags = list(map(lambda t: t['title'], self._json['photo_tags']))
		else:
			self.photo_tags = None
		
		Urls = namedtuple('Urls', 'raw full regular small thumb')
		self.urls = Urls(**self._json['urls'])

		self.created_at = dateutil.parser.parse(self.created_at)

		if hasattr(self, 'updated_at'):
			self.updated_at = dateutil.parser.parse(self.updated_at)
		else:
			self.updated_at = None

		if 'location' in self._json:
			Location = namedtuple('Location', 'title name city country position')
			Position = namedtuple('Position', 'latitude longitude')
			json_loc = dict(self._json['location'])
			json_loc.pop('position')
			self.location = Location(**json_loc, position=Position(**self._json['location']['position']))
		else:
			self.location = None

		if 'exif' in self._json:
			Exif = namedtuple('Exif', 'make model exposure_time aperture focal_length iso')
			self.exif = Exif(**self._json['exif'])
		else:
			self.exif = None

		if not from_user:
			self.from_user = User(self._json['user']['username'])

	@classmethod
	def from_json(cls, _json):
		return cls(_json['id'], _json=_json)

	@classmethod
	def from_json_text(cls, json_text):
		_json = json.loads(json_text)
		return cls.from_json(_json)

	@classmethod
	def from_json_file(cls, json_file):
		with open(json_file) as f:
			return cls.from_json_text(f.read())

	@classmethod
	def random(cls):
		req = requests.get(urljoin(_napiUrl, 'photos/random'))
		return cls.from_json_text(req.text)

	def save_json_data(self, location=None):
		if not location:
			with open('photo-info-{}.json'.format(self.id), 'w') as f:
				f.write(json.dumps(self._json, indent=4))

	def download(self, size='regular', download_location=None):
		dwld_url = self.urls._asdict()[size]
		photo_content = requests.get(dwld_url).content
		location_and_name = '{}-{}'.format(self.id, size) if not download_location else download_location

		if not os.path.exists(location_and_name):
			with open(location_and_name, 'wb') as photo:
				photo.write(photo_content)

class User:

	def __init__(self, username, get_total_info=True):
		super().__init__()
		self.id = None
		self.username = username
		self.api_url = urljoin(_napiUrl, 'users/{}'.format(self.username))

		if get_total_info:
			res = requests.get(self.api_url).text
			self._json = json.loads(res)

			json_to_attrs(self, self._json)

			if hasattr(self, 'updated_at'):
				self.updated_at = dateutil.parser.parse(self.updated_at)
			if 'tags' in self._json:
				if 'custom' in self._json['tags']:
					self.interests = list(map(lambda t: t['title'], self._json['tags']['custom']))
				if 'aggregated' in self._json['tags']:
					self.aggregated_tags = list(map(lambda t: t['title'], self._json['tags']['aggregated']))	
	
	def profile_image(self, size: Union['small', 'medium', 'large']='medium', w=None, h=None):
		ProfileImage = namedtuple('ProfileImage', 'small medium large')
		profile_img_urls = ProfileImage(**self._json['profile_image'])

		if size in profile_img_urls._asdict():
			if not w and not h:
				return profile_img_urls._asdict()[size]
			elif w and h:
				p = re.compile(r'h=\d+&w=\d+')
				return p.sub('h={}&w={}'.format(h, w), profile_img_urls.small)
			else:
				raise NotImplementedError('If you want a custom image dimension you must provide both w and h')
		else:
			raise NotImplementedError('The size provided is not valid. Try using "small", "medium" or "large"')

	@property
	def photos(self):
		total_pages = math.ceil(self.total_photos / 20)
		for pnum in range(1, total_pages + 1):
			res = requests.get(urljoin(_napiUrl, 'users/{}/photos?page={}&per_page=20&order_by=latest'.format(self.username, pnum)))
			res_json = json.loads(res.text)
			for p in res_json:
				yield p