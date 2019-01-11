import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="unsplashpy",
    version="1.0",
    author="Saul Dominguez",
    author_email="saulydominguez@gmail.com",
    description="A Unsplash client without the need for an api key",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sauldom102/unsplashpy",
	py_modules=['unsplashpy', ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)