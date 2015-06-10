# sefara

Sefara is a small Python library to help manage the datasets used in scientific analysis projects.

You might consider using Sefara if you find yourself:
 * hard coding paths and metadata for input files in analysis scripts or IPython notebooks
 * copy and pasting paths from a spreadsheet into the shell to run commandline tools
 * defining lots of environment variables giving paths to commonly analyzed datasets

Sefara improves over these common workflows by providing programmatic and commandline interfaces for specifying, grouping, and filtering datasets.

Sefara works well for analyses involving hundreds to perhaps a few thousand datasets. If you need to manage many more datasets than that, you probably need a more sophisticated solution.

## Defining a resource collection

We use the term "resource" to mean any entity used in an analysis. In practice resources usually correspond to files on a filesystem, but sefara makes no assumptions about this. 

Users define a "resource collection" in a file that sefara reads. Two formats are supported for resource collection files: executable Python and JSON.

Here's an example resource collection with two resources, defined using Python:

```
from sefara import export
export(
    "patientA_sequencing_blood_2010",
    path="/path/to/file1.bam",
    tags=["patient_A", "sequencing", "2010"],
    capture_kit="Agilent sureselect",
    description="Sample taken from normal blood"
)

export(
    "patientA_sequencing_tumor_2012",
    path="/path/to/file2.bam",
    tags=["patient_A", "sequencing", "2012"],
    capture_kit="Nimblegen",
    description="Primary tumor, left ovary"
)
```

This defines two resources named `patientA_sequencing_blood_2010` and `patientA_sequencing_tumor_2012`. Sefara resources always have a `name` attribute (the first parameter to the `export` function). Everything else is optional. If you define a `tags` attribute for your resource, as in the file above, then Sefara treats that attribute specially, as we'll see below. All the other fields (like `path` and `capture_kit`) are up to the user and are not interpreted by Sefara in any way.

We could also have defined these resources by making a JSON file, like this:

```
{
    "patientA_sequencing_blood_2010": {
        "tags": [
            "sequencing",
            "patient_A",
            "2010"
        ],
        "capture_kit": "Agilent sureselect",
        "path": "/path/to/file1.bam",
        "description": "Sample taken from normal blood"
    },
    "patientA_sequencing_tumor_2012": {
        "tags": [
            "sequencing",
            "patient_A",
            "2012"
        ],
        "capture_kit": "Nimblegen",
        "path": "/path/to/file2.bam",
        "description": "Primary tumor, left ovary"
    }
}
```

## Two commandline tools: sefara-select and sefara-dump

Use 



## Opening a resource collection in Python




## Site-specific configuration with hooks




This is currently a very rough cut, not ready for general use. More soon.

The [test/data](test/data) directory has some example resource files.

Example code:

```
resources = sefara.load("test/data/ex1.py")
for resource in resources.filter("tags.gamma"):
    print("%s = %s" % (resource.name, resource.path))
```
