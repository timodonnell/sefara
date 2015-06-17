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
    description="Practical dataset management",
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            'sefara-select = sefara.commands.select:run',
            'sefara-dump = sefara.commands.dump:run',
            'sefara-check = sefara.commands.check:run',
            'sefara-env = sefara.commands.env:run',
        ]
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
    ],
    install_requires=[
        "attrdict>=2.0.0",
        "nose>=1.3.1",
        "typechecks>=0.0.2",
        "future>=0.14.3",
        "pandas>=0.16.1",
    ]
)
