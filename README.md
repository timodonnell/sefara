# sefara

Sefara is a simple Python library to help manage the datasets used in scientific analysis projects.

In our work in genomics at Hammer Lab, we commonly 

## Defining a resource collection

Sefara can read and write resource collections as either executable python code or JSON. Here's an example resource collection defined using Python:


and here is the equivalent JSON:


## Opening a resource collection in Python


## Two commandline tools: sefara-select and sefara-dump


## Site-specific configuration with hooks




This is currently a very rough cut, not ready for general use. More soon.

The [test/data](test/data) directory has some example resource files.

Example code:

```
resources = sefara.load("test/data/ex1.py")
for resource in resources.filter("tags.gamma"):
    print("%s = %s" % (resource.name, resource.path))
```
