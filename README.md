# sefara

Sefara is a Python library to help manage the datasets in a scientific analysis projects.

Users write a json (or [hjson](http://hjson.org/)) description of their "resources" under analysis. Sefara gives a Python API to filter and query these files. No assumptions are made about what these "resources" correspond to. In our use case, each resource describes a BAM or VCF file in a bioinformatics analysis.

We anticipate adding a commandline tool soon for working with resource files in the shell.

This is currently a very rough cut, not ready for general use.

The [test/data](test/data) directory has some example resource files.

Example Python code:
```
resources = sefara.load("test/data/ex1.hjson")

for resource in resources.with_tag("delta"):
    print("%s = %s" % (resource.name, resource.path))
```