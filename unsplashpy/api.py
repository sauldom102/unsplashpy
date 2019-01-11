import requests, json, math, os, time
from urllib.parse import urljoin
from threading import Thread, Lock
from queue import Queue
from typing import Union

from unsplashpy.constants import _napiUrl

from unsplashpy.photos import Photo

class Unsplash:

	def __init__(self, size_to_download:Union['thumb', 'small', 'regular', 'full']='regular'):
		self.images_count_lock = Lock()
		self.images_downloaded_count = 0
		self.last_search_text = None
		self.size_to_download = size_to_download
		self.urls = Queue()

	def search(self, text:str, per_page:int=30, debug:bool=True):
		first_page = requests.get(urljoin(_napiUrl, 'search/photos?query={}&xp=&per_page={}&page=1'.format(text.replace(' ', '%20'), per_page)))
		
		if first_page.ok:
			json_res = json.loads(first_page.text)

			self.last_search_text = text
	
			self.last_search_total_photos, self.last_search_total_pages = json_res['total'], json_res['total_pages']
			if debug:
				print('There are {} photos and {} pages for searching text "{}"'.format(self.last_search_total_photos, self.last_search_total_pages, text))

	def _add_urls(self, num_pages:int=10):
		if self.last_search_text:
			self.urls = Queue(num_pages)

			for i in range(1, num_pages+1):
				self.urls.put(urljoin(_napiUrl, 'search/photos?query={}&xp=&per_page=30&page={}'.format(self.last_search_text.replace(' ', '%20'), i)))

	def _get_images(self, num_pages:int):	
		for _ in range(num_pages):
			url = self.urls.get()
			req = requests.get(url)
			json_res = json.loads(req.text)

			for res in json_res['results']:
				photo = Photo.from_json(res)
				photo.download(self.size_to_download, self.last_search_text)

				with self.images_count_lock:
				 	self.images_downloaded_count += 1

			self.urls.task_done()

	def download_last_search(self, num_pages:int=10, image_size: Union['thumb', 'small', 'regular', 'full']='regular', max_num_threads=200, debug=True):
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
