import requests, json, math, os, time
import dateutil.parser
from threading import Thread, Lock
from queue import Queue

class Unsplash:

	rootUrl = 'https://unsplash.com/napi/'

	def __init__(self, size_to_download='regular'):
		self.images_count_lock = Lock()
		self.images_downloaded_count = 0
		self.last_search_text = None
		self.size_to_download = size_to_download
		self.urls = Queue()

	def search(self, text, per_page=30, debug=True):
		first_page = requests.get('{}search/photos?query={}&xp=&per_page={}&page=1'.format(self.rootUrl, text.replace(' ', '%20'), per_page))
		
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
				self.urls.put('{}search/photos?query={}&xp=&per_page=30&page={}'.format(self.rootUrl, self.last_search_text.replace(' ', '%20'), i))

	def _get_images(self, num_pages):	
		for _ in range(num_pages):
			url = self.urls.get()
			print(url)
			req = requests.get(url)
			json_res = json.loads(req.text)

			for res in json_res['results']:
				image_url = res['urls'][self.size_to_download]
				image_path = '{}/{}-{}'.format(self.last_search_text, res['id'], self.size_to_download)

				if not os.path.exists(image_path):
					with open(image_path, 'wb') as im:
						im.write(requests.get(image_url).content)
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
	
	def __init__(self, json=None, from_user=None, id=None):
		self.id = id
		self._json = json
		self.from_user = from_user

class User(Unsplash):

	def __init__(self, username, get_total_info=True):
		super().__init__()
		self.id = None
		self.username = username
		self.api_url = '{}users/{}'.format(self.rootUrl, self.username)

		if get_total_info:
			res = requests.get(self.api_url).text
			json_res = json.loads(res)

			for key, val in json_res.items():
				if type(val) in (str, int, type(None) ):
					setattr(self, key, val if type(val) is not str else val.strip())

			self.updated_at = dateutil.parser.parse(self.updated_at)	

	@property
	def photos():
		# TODO: Add call to fetch all user photos	

if __name__ == '__main__':
	u = Unsplash()

	search_text = input('Tell me what are you searching for: ')
	u.search(search_text)

	num_pages = input('Pages to download [5]: ')
	num_pages = 5 if num_pages == '' else int(num_pages)

	image_size = input('Image size to download (full, regular, small, thumb) [regular]: ')
	image_size = 'regular' if image_size == '' else image_size

	u.download_last_search(num_pages=num_pages, image_size=image_size)