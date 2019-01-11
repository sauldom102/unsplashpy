import requests
import json
import re
from urllib.parse import urljoin
from typing import Union
from collections import namedtuple
import dateutil.parser

from unsplashpy.constants import _napiUrl
from unsplashpy.utils import json_to_attrs

class UserNotFoundException(Exception):
	"""Raised when trying to find a user who doesn't exists"""
	pass

class User:

	def __init__(self, username:str, get_total_info:bool=True, _json:dict=None):
		super().__init__()
		self.id = None
		self.username = username
		self.api_url = urljoin(_napiUrl, 'users/{}'.format(self.username))
		self._json = _json

		if _json:
			json_to_attrs(self, _json)

		if get_total_info:
			res = requests.get(self.api_url).text
			self._json = json.loads(res)

			if 'errors' in self._json:
				raise UserNotFoundException('\n'.join(self._json['errors']))

			json_to_attrs(self, self._json)

			if hasattr(self, 'updated_at'):
				self.updated_at = dateutil.parser.parse(self.updated_at)
			if 'tags' in self._json:
				if 'custom' in self._json['tags']:
					self.interests = list(map(lambda t: t['title'], self._json['tags']['custom']))
				if 'aggregated' in self._json['tags']:
					self.aggregated_tags = list(map(lambda t: t['title'], self._json['tags']['aggregated']))	
	
	@classmethod
	def from_json(cls, _json:dict, get_total_info=True):
		return cls(_json['username'], get_total_info=get_total_info, _json=_json)

	def profile_image(self, size: Union['small', 'medium', 'large']='medium', w:int=None, h:int=None):
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
				yield Photo.from_json(p)

	def download_all_photos(self, photo_size='regular', dwnld_location=None):
		download = lambda p: p.download(size=photo_size, download_location=self.username if not dwnld_location else dwnld_location)

		threads = []
		for p in self.photos:
			t = Thread(target=download, args=(p, ))
			t.start()
			threads.append(t)

		for t in threads:
			t.join()