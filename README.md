# sefara

Sefara is a Python library to help manage the datasets in a scientific analysis projects.

This is currently a very rough cut, not ready for general use. More soon.

The [test/data](test/data) directory has some example resource files.

Example code:

```
resources = sefara.load("test/data/ex1.py")
for resource in resources.filter("tags.gamma"):
    print("%s = %s" % (resource.name, resource.path))
```
