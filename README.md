# Unsplashpy

## Description

An Unsplash client without the need for an api key. For a full documentation visit <https://sauldom102.github.io/unsplashpy>.

## Getting started

You can try out how this module works by importing the Unsplash class, which will help you with some user regular actions as searching for a keyword and then download a certain number of image pages of that results.

```python
from unsplashpy import Unsplash

u = Unsplash()

search_text = input('Tell me what are you searching for: ')
u.search(search_text)

num_pages = input('Pages to download [10]: ')
num_pages = 5 if num_pages == '' else int(num_pages)

image_size = input('Image size to download [regular]: ')
image_size = 'regular' if image_size == '' else image_size

u.download_last_search(num_pages=num_pages, image_size=image_size)
```

## Some examples

### Download user's photos

The bellow code will allow you to download all the user's published photos. One difference from the "Quick start" example is that this will take much more time downloading all pictures because this part doesn't make use of multithreading. We'll see another example on how to make this in a much more efficient way.

Another thing to know is that, by default, all the images downloaded will have a regular resolution.

``` py3
from unsplashpy import User

username = input('Tell me a username: ')
u = User(username)

for p in u.photos:
    p.download(download_location=username)
```

### Download user's photos (multithreading way)

As said before, this is a more efficient way to download photos. It takes much less time than the above example.

``` py3
from unsplashpy import User

username = input('Tell me a username: ')
u = User(username)
u.download_all_photos()
```

### Download random photo

``` py3
from unsplashpy import Photo

p = Photo.random()
p.download()
```