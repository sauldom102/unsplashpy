import requests, json, math
from urllib.parse import urljoin

from unsplashpy.constants import _napiUrl
from unsplashpy.utils import json_to_attrs

from unsplashpy.photos import Photo
from unsplashpy.users import User

class Collection:

	def __init__(self, id):
		self.id = id
		self.api_url = urljoin(_napiUrl, 'collections/{}'.format(self.id))

		res = requests.get(self.api_url)
		self._json = json.loads(res.text)

		json_to_attrs(self, self._json)

		if 'tags' in self._json:
			self.tags = [t['title'] for t in self._json['tags']]

		self.cover_photo = Photo.from_json(self._json['cover_photo'])

	def from_user(self, get_total_info:bool=True):
		if not hasattr(self, '_from_user'):
			self._from_user = User.from_json(self._json['user'], get_total_info=get_total_info)
			return self._from_user
		
		return self._from_user

	@property
	def photos(self):
		total_pages = math.ceil(self.total_photos / 20)
		for pnum in range(1, total_pages + 1):
			res = requests.get(urljoin(_napiUrl, 'collections/{}/photos?page={}&per_page=20&order_by=latest'.format(self.id, pnum)))
			res_json = json.loads(res.text)
			for p in res_json:
				yield Photo.from_json(p)