Tutorial
==============================

Creating a resource collection
------------------------------

A "resource" describes an entity used in an analysis. Resources
often point to files on a filesystem, but sefara makes no assumptions
about this. Sefara is a tool for managing resources.

Users define a "resource collection" in a file that sefara reads. Two
formats are supported for these files: executable Python and JSON.

Here's a resource collection defined using Python:

.. literalinclude:: resource-collections/ex1.py

This defines five resources named ``patientA_sequencing_blood_2010``,
``patientA_sequencing_tumor_2012``, and so on (this example is from a cancer DNA sequencing analysis).

Sefara resources always have a ``name`` attribute, given as the first parameter to the ``export`` function.
Everything else is optional. If you define a ``tags`` attribute for your
resource, as in the file above, then Sefara treats that attribute slightly
specially, as we'll see below. All the other fields (like ``path`` and
``capture_kit``) are up to the user and are not interpreted by Sefara in
any way.

.. note::
    Using Python as a configuration language for resource collections has pros and cons. Python enables concise descriptions of collections that have repetitive structure. However, full-fledged programs can be difficult to debug and maintain.

    The best practice is to keep collection files very simple. Loops and string manipulation are fine, but libraries, filesystems, or network services should be avoided.

    If you find yourself writing a complex Python script to define a collection, consider instead writing a script that *creates* the collection. That script can be called once to write out a collection (in either Python or JSON format), to be used for subsequent analysis.

We could also have defined these resources in JSON file. Here is the same collection defined using JSON:

.. program-output:: sefara-dump resource-collections/ex1.py

Opening a resource collection in Python
---------------------------------------

The collection shown before can be opened in Python using `sefara.load`:

.. runblock:: pycon

    >>> import sefara
    >>> resources = sefara.load("resource-collections/ex1.py")
    >>> print(resources)

To get a detailed summary of each resource, use the `ResourceCollection.summary` property:

.. runblock:: pycon
    >>> resources.summary

Individual resources in a collection can be accessed by name or index:

.. runblock:: pycon

    >>> resources["patientA_sequencing_tumor_2012"]
    >>> resources[0]

Use `Resource.select` to pick out certain fields, as a pandas dataframe:

.. runblock:: pycon

    >>> resources.select("name", "path")

By default, if you try to select a field that doesn't exist in some resource, you'll get an exception. To instead skip these resources, pass ``if_error="skip"`` to `select`. Here, we'll skip the last resource, which has no "capture_kit" field.

.. runblock:: pycon

    >>> resources.select("name", "capture_kit", if_error="skip")


Everything is a Python expression
---------------------------------------






Two tools: sefara-select and sefara-dump
---------------------------------------------------- 

The ``sefara-select`` tool extracts fields from a sefara collection.





Use



Site-specific configuration with hooks
--------------------------------------

This is currently a very rough cut, not ready for general use. More
soon.

The `test/data <test/data>`__ directory has some example resource files.

Example code:

::

    resources = sefara.load("test/data/ex1.py")
    for resource in resources.filter("tags.gamma"):
        print("%s = %s" % (resource.name, resource.path))