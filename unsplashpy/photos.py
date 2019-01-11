import requests
import json
import os
import dateutil.parser
from urllib.parse import urljoin
from typing import Union
from collections import namedtuple

from unsplashpy.users import User

from unsplashpy.constants import _napiUrl
from unsplashpy.utils import json_to_attrs

class Photo:
	
	def __init__(self, id:str, _json:dict=None):
		self.id = id
		self._json = _json
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

	@property
	def from_user(self, get_total_user_info:bool=True):
		if not hasattr(self, '_from_user'):
			self._from_user = User(self._json['user']['username'], get_total_info=get_total_user_info)
			return self._from_user
		
		return self._from_user

	@classmethod
	def from_json(cls, _json:dict):
		return cls(_json['id'], _json=_json)

	@classmethod
	def from_json_text(cls, json_text:str):
		_json = json.loads(json_text)
		return cls.from_json(_json)

	@classmethod
	def from_json_file(cls, json_file:str):
		with open(json_file) as f:
			return cls.from_json_text(f.read())

	@classmethod
	def random(cls):
		req = requests.get(urljoin(_napiUrl, 'photos/random'))
		return cls.from_json_text(req.text)

	def save_json_data(self, location:str=None):
		with open(os.path.join('' if not location else location, 'photo-info-{}.json'.format(self.id)), 'w') as f:
			f.write(json.dumps(self._json, indent=4))

	def download(self, size='regular', download_location:str=None):
		dwld_url = self.urls._asdict()[size]
		photo_content = requests.get(dwld_url).content
		complete_path = os.path.join('' if not download_location else download_location, '{}-{}'.format(self.id, size))

		if download_location and not os.path.isdir(download_location):
			os.mkdir(download_location)

		if not os.path.exists(complete_path):
			with open(complete_path, 'wb') as photo:
				photo.write(photo_content)
