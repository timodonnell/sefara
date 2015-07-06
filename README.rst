sefara
======

Sefara is a Python library for managing your datasets. It provides a way to specify once what your datasets are (usually fileystem paths) and any metadata (e.g. which experiment they came from), then refer to them conveniently in analysis scripts and notebooks.

Sefara doesn't assume anything about what your datasets are, what format they're in, or are how they are accessed.

Quick example
-------------
Define a "resource collection" by making a file like this, which we'll call ``datasets.sefara.py``:

::

    from sefara import export

    export(
        "my_first_dataset.hdf5",
        path="/path/to/file1.hdf5",
        tags=["first", "important"],
    )
    export(
        "my_second_dataset.csv",
        path="/path/to/file2.csv",
        tags=["second", "unimportant"],
    )

Then, use Sefara to open it in Python:

::

    >>> import sefara
    >>> datasets = sefara.load("datasets.sefara.py")
    >>> print(datasets.filter("tags.important")[0].path)
    /path/to/file1.hdf5

Documentation
-------------
Available at: http://timodonnell.github.io/sefara/docs/html

Installation
-------------
::

    pip install sefara

To run the tests:

::

    nosetests

To build the documentation:

::

    pip install -e .
    pip install Sphinx
    cd docs
    make clean setup rst html

The docs will be written to the ``_build/html`` directory.

