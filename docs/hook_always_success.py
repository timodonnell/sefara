import os

def check(collection):
    for (i, resource) in enumerate(collection):
        if i == int(os.environ.get("FAILURE_NUM", -1)):
            try:
                with open(resource.path):
                    pass
            except Exception as e:
                # Failure
                message = "Couldn't open path: %s" % e
                yield (resource, True, message)
        else:
            yield (resource, True, None)


