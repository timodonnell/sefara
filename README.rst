sefara
======

Sefara is a small Python library for managing datasets and their metadata.

If your data analysis project is using spreadsheets, environment variables, or hard-coded paths in scripts to keep track of your datasets, try Sefara.

Sefara gives programmatic and commandline interfaces for working with descriptions of datasets, called "resources." Resources are specified in text files as either JSON or Python code. Sefara doesn't assume anything about what your datasets are (for example, files or database records) or how to access it them.

The use case is to manage the ~10 to ~1,000 datasets that commonly go into a single publication. Sefara is good for answering **what datasets went into this plot?** but not **what datasets are available at my institution?** It's complimentary to any scientific workflow management system you may be using.

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

    cd docs
    pip install Sphinx
    make clean setup rst html

The docs will be available in the ``_build/html`` directory.

