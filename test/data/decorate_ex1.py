# This is an example decorator.

def default(resource_collection):
    for resource in resource_collection:
        resource.posix_path = "/path/to/%s.bam" % resource.name
