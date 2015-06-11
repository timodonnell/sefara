Tutorial
==============================

Resources
------------------------------

We use the term "resource" to mean any entity used in an analysis. In
practice resources usually correspond to files on a filesystem, but
sefara makes no assumptions about this.

Users define a "resource collection" in a file that sefara reads. Two
formats are supported for resource collection files: executable Python
and JSON.

Here's an example resource collection with two resources, defined using
Python:

.. literalinclude:: resource-collections/ex1.py

This defines two resources named ``patientA_sequencing_blood_2010`` and
``patientA_sequencing_tumor_2012``. Sefara resources always have a
``name`` attribute (the first parameter to the ``export`` function).
Everything else is optional. If you define a ``tags`` attribute for your
resource, as in the file above, then Sefara treats that attribute
specially, as we'll see below. All the other fields (like ``path`` and
``capture_kit``) are up to the user and are not interpreted by Sefara in
any way.

We could also have defined these resources by making a JSON file, like
this:

.. program-output:: sefara-dump resource-collections/ex1.py


Two commandline tools: sefara-select and sefara-dump
----------------------------------------------------

Use

Opening a resource collection in Python
---------------------------------------

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