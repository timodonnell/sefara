Tutorial
==============================

Motivation
------------------------------

We've all found ourselves hard coding paths to input files in analysis scripts and notebooks. Putting paths and metadata in spreadsheets is an improvement, but still requires significant code to work with conveniently and doesn't handle multiple, loosely defined schemas. Databases are probably the right solution for huge projects but are inconvenient at smaller scale.

With Sefara, you write Python code to specify the files you're analyzing and their metadata. Defining your datasets with code may seem strange but it allows for a lot flexibility. These files describing your datasets are called "resource collections" and can be put under version control and in general treated like code. Sefara is a Python library and a few commandline tools for reading, writing, and querying these files.

Resource collections
------------------------------

Creating
+++++++++++++++++++++++++++++++

A "resource" describes an entity used in an analysis. Resources
often point to files on a filesystem.

Users define a "resource collection" in a file that sefara reads. Two
formats are supported for these files: executable Python and JSON.

Here's a resource collection defined using Python:

.. literalinclude:: resource-collections/ex1.py

This defines five resources named ``patientA_sequencing_blood_2010``,
``patientA_sequencing_tumor_2012``, and so on (this example is from a cancer DNA sequencing analysis).

Sefara resources always have a ``name`` attribute, given as the first parameter to the `export` function.
Everything else is optional. If you define a ``tags`` attribute for your
resource, as in the file above, then Sefara treats that attribute slightly
specially, as we'll see below. All the other fields (like ``path`` and
``capture_kit``) are up to the user and are not interpreted by Sefara in
any way.

.. note::
    Using Python as a configuration language for resource collections has pros and cons. Python enables concise descriptions of collections that have repetitive structure. However, full-fledged programs can be difficult to debug and maintain.

    The best practice is to keep collection files very simple. Loops and string manipulation are fine, but using libraries, filesystems, or network services should be avoided.

    If you find yourself writing a complex Python script to define a collection, consider instead writing a script that *creates* the collection. That script can be called once to write out a collection (in either Python or JSON format), to be used for subsequent analysis.



Opening
+++++++++++++++++++++++++++++++

The collection shown before can be opened in Python using `sefara.load`:

.. runblock:: pycon

    >>> import sefara
    >>> resources = sefara.load("resource-collections/ex1.py")
    >>> print(resources)

To get a detailed summary of each resource, use the `ResourceCollection.summary` property:

.. runblock:: pycon

    >>> print(resources.summary)

Individual resources in a collection can be accessed by name or numeric index:

.. runblock:: pycon

    >>> resources["patientA_sequencing_tumor_2012"]
    >>> resources[0]

Each `Resource` is a dict-like object (an `AttrDict`). You can access fields in the resource using either brackets (``resource["name"]``) or attributes (``resource.name``).

You can iterate over a resource collection to get each resource in turn:

.. runblock:: pycon

    >>> for resource in resources.filter("tags.patient_A"):
    ...        print(resource.path)

Here we used the `filter` method, described next.

Filtering
+++++++++++++++++++++++++++++++

The `filter` method returns a new `ResourceCollection` with only the resources for which a Python expression evaluates to ``True``:

.. runblock:: pycon

    >>> resources.filter("capture_kit == 'Nimblegen'")

The expressions are evaluated with the resource's attributes as local variables. Here's another example:

.. runblock:: pycon

    >>> resources.filter("tags.patient_A")

Here we used the fact that sefara handles a resource attribute called ``tags`` a bit specially. If your resource has an attribute called ``tags`` giving a list of strings, it becomes an instance of `Tags`, a class that inherits from Python's `set` class, but also provides attribute-style access for membership testing.

Simple expressions combining tags are a convenient way to filter collections:

.. runblock:: pycon

    >>> resources.filter("tags.patient_A and not tags.sequencing")

Instead of a string expression, you can also pass a Python callable to `filter`:

.. runblock:: pycon

    >>> resources.filter(lambda resource: resource.tags.variants)

Selecting
+++++++++++++++++++++++++++++++

Use `ResourceCollection.select` to pick out fields across a collection
in a `pandas.DataFrame`:

.. runblock:: pycon

    >>> resources.select("name", "path")

You can pass Python expressions to `select`:

.. runblock:: pycon

    >>> resources.select("name.upper()", "os.path.basename(path)")

To set the column names in the dataframe, give a "name: expression" string:

.. runblock:: pycon

    >>> resources.select("name: name.upper()", "filename: os.path.basename(path)")

To select one column as a pandas series instead of a dataframe, use `select_series`:

.. runblock:: pycon

    >>> resources.select_series("path")


Loading with URLs and filters
+++++++++++++++++++++++++++++++

The `sefara.load` function supports two other features worth knowing about:

 - you can pass an http or https URL.
 - you can specify a filter as part of the filename.

The syntax for filtering is "<filename>#filter=<filter expression>". Here's an example:

.. runblock:: pycon

    >>> sefara.load("resource-collections/ex1.py#filter=tags.variants")

This comes in handy for analysis scripts that take a resource collection as a commandline argument. If the script passes the argument to `load`, then it automatically supports filtering.

Outputting a resource collection
++++++++++++++++++++++++++++++++++

The `ResourceCollection.to_python` method gives string of Python code representing the collection:

.. runblock:: pycon

    >>> print(resources.filter("tags.patient_B").to_python())

See the `write` method for a convenient way to write this to a file.


JSON
+++++++++++++++++++++++++++++++++++++++++++++++++

Resource collections can also be specified with JSON. They are loaded with `load` the same way as python collections, and there is a `ResourceCollection.to_json` method to get the JSON representation of any collection.

Here's what the same collection from before looks like using JSON:

.. program-output:: sefara-dump resource-collections/ex1.py


Commandline tools
---------------------------------------------------- 

sefara-dump
+++++++++++++++++++++++++++++++++++++++++++++++++

The `sefara-dump` tool is a utility for reading in a collection and writing it out again after filtering, transforming, or changing the format. For example, we can write out a filtered version of our example collection:

.. command-output:: sefara-dump resource-collections/ex1.py --filter tags.patient_B --format python

Or in JSON format:

.. command-output:: sefara-dump resource-collections/ex1.py --filter tags.patient_B --format json

The ``--code`` argument is an experimental feature that makes it possible to add, remove, and modify
attributes of the collection by specifying Python code on the commandline. For example, we can capitalize
all the resource names like this:

.. command-output:: sefara-dump resource-collections/ex1.py --code 'name = name.upper()'



sefara-select
+++++++++++++++++++++++++++++++++++++++++++++++++

The `sefara-select` tool picks out fields in your collection and gives results in CSV or a few other formats:

.. command-output:: sefara-select resource-collections/ex1.py name path

Like the `select` method, you can also use Python expressions, and set the column names:

.. command-output:: sefara-select resource-collections/ex1.py name 'filename: os.path.basename(path)'

Filters are supported:

.. command-output:: sefara-select resource-collections/ex1.py name --filter tags.patient_B

If you only select one field, by default no header is printed. That's convenient for writing shell loops like this:

.. command-output:: for p in $(sefara-select resource-collections/ex1.py path) ; do ls $p ; done
    :shell: 

The tool provides rudimentary support for building up argument lists, suitable for passing to analysis scripts that don't use sefara. Here's an example (note that the first line is the command we typed -- the second line is the output of the command, which is an argument string):

.. command-output:: sefara-select resource-collections/ex1.py name path --format args

and another:

.. command-output:: sefara-select resource-collections/ex1.py 'filename:path' --format args-repeated



.. command-output:: python -c 'import sys; print("\n".join(sys.argv[1:]))' $(sefara-select resource-collections/ex1.py path --format args-repeated)
    :shell:

Note that for any sefara tool (and the `load` function), you can pass ``-`` as a path to a resource collection to read from stdin.

With creative use of the ``--code`` argument to `sefara-dump` and piping the results to `sefara-select`, it's often possible to munge a resource collection into the argument format your tool expects.

.. command-output:: python -c 'import sys; print(sys.argv)' $(sefara-dump resource-collections/ex1.py --code 'kind = os.path.splitext(path)[1]' | sefara-select - kind path --format args-repeated 
    :shell:



Advanced functionality
---------------------------------------------------- 



Things to be aware of
+++++++++++++++++++++++++++++++++++++++++++++++++

If you `select` or `filter` by a field that exists in some resources but not others, it defaults to ``None`` in the resources where it is missing:

.. runblock:: pycon

    >>> resources.select("name", "capture_kit")



Site-specific configuration with hooks
+++++++++++++++++++++++++++++++++++++++++++++++++


This is currently a very rough cut, not ready for general use. More
soon.

The `test/data <test/data>`__ directory has some example resource files.

Example code:

::

    resources = sefara.load("test/data/ex1.py")
    for resource in resources.filter("tags.gamma"):
        print("%s = %s" % (resource.name, resource.path))