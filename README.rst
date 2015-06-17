sefara
======

Sefara is a small Python library for managing dataset metadata.

If your data analysis project is using spreadsheets, environment variables, or hard-coded paths in scripts to keep track of your datasets, you might consider using Sefara.

Sefara gives programmatic and commandline interfaces for working with descriptions of datasets, called "resources." Resources are specified in text files as either JSON or Python code. Sefara doesn't assume anything about what your datasets are or are how they are accessed.

The use case is to manage the ~10 to ~1,000 datasets that commonly go into a single publication. Sefara is good for answering **what datasets went into this plot?** but not **what datasets are available at my institution?** It's complimentary to any scientific workflow management system you may be using.

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

Then, load it up in Python:

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
From a git checkout, run:

::

    pip install .

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

