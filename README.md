# Description

A Unsplash client without the need for an api key

# Getting started

You can start try out how this module works by importing the Unsplash class, which will help you with some user regular actions as searching for a keyword and then download a certain number of image pages of that results

```python
from unsplash import Unsplash

u = Unsplash()

search_text = input('Tell me what are you searching for: ')
u.search(search_text)

num_pages = input('Pages to download [10]: ')
num_pages = 5 if num_pages == '' else int(num_pages)

image_size = input('Image size to download [regular]: ')
image_size = 'regular' if image_size == '' else image_size

u.download_last_search(num_pages=num_pages, image_size=image_size)
```
