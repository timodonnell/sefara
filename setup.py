try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="sefara",
    version="0.0.0",
    author="Tim O'Donnell",
    author_email="timodonnell@gmail.com",
    packages=["sefara"],
    url="https://github.com/timodonnell/sefara",
    license="Apache License",
    description="Simple library to keep track of datasets",
    long_description=open('README.md').read(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],
)
