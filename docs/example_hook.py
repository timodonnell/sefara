import os

def check(collection):
    '''
    Check that all resources with a ``path`` attribute specify a valid path
    that exists on the filesystem.

    For each resource in the collection, we yield a tuple:

        (resource, attempted, problem)
    
    where:
        
        resource : `Resource`
            the `Resource` instance

        attempted : boolean
            whether we attempted to validate this resource. We only attempt to
            validate resources that have a ``path`` attribute.

        problem : string or None
            None if validation was successful, error message if validation failed
    '''

    for resource in collection:
        if 'path' in resource:
            try:
                with open(resource.path):
                    pass
            except Exception as e:
                # Failure
                message = "Couldn't open path: %s" % e
                yield (resource, True, message)
            else:
               # Success
               yield (resource, True, None)
        else:
            # Can't validate this resource.
            yield (resource, False, "No path specified.")

def transform(collection):
    '''
    For resources that have a 'path' attribute pointing to a certain
    subdirectory, add a "http_url" attribute.
    '''
    for resource in collection:
        if 'path' in resource and resource.path.startswith("/path/to"):
            # Add http_url
            resource.http_url = "http://our-internal-file-server" + resource.path


