import re, hjson, attrdict

def check_valid_tag(tag):
    if re.match('^[\w][\w-]+$', tag) is None:
        raise ValueError("Invalid tag: %s" % tag)

def load(filename):
    if filename.endswith(".hjson"):
        with open(filename) as fd:
            data = hjson.load(fd)
    else:
        raise ValueError("Unsupported file type: %s" % filename)

    resources = []
    for d in data['resources']:
        if 'name' not in d:
            d['name'] = "_resource_%d" % len(resources)
        d['tags'] = set(d.get('tags', []))
        for tag in d['tags']:
            check_valid_tag(tag)
        resources.append(attrdict.AttrDict(d))
    
    common = attrdict.AttrDict(data.get("common", {}))
    return ResourceCollection(resources, common, filenames = set([filename]))

def label_strings(strings):
    result = {True: set(), False: set()}
    for string in strings:
        result[True].add(string[1:])
    if string.startswith("-"):
        result[False].add(string[1:])
    else:
        result[True].add(string)
    return result

class ResourceCollection:
    def __init__(self, resources, common = None, filenames = None):
        if common is None:
            common = {}
        if filenames is None:
            filenames = set()
            
        self.resources = [attrdict.AttrDict(resource) for resource in resources]
        self.common = attrdict.AttrDict(common)
        self.filenames = filenames
        for resource in self.resources:
            resource.common = common
        
    def derive(self, common = None, resources = None):
        if common is None:
            common = self.common
        if resources is None:
            resources = self.resources
        elif callable(resources):
            resources = [resources(resource) for resource in self.resources]
        return ResourceCollection(resources, common, self.filenames)
    
    def with_tag(self, *tags):
        labeled = label_strings(tags)
        return self.derive(resources = [
            resource
            for resource in self.resources
            if any(tag in resource.tags for tag in labeled[True]) or
               any(tag not in resource.tags for tag in labeled[False])
        ])
    
    def with_name(self, *names):
        labeled = label_strings(names)
        
        return self.derive(resources = [
            resource
            for resource in self.resources
            if resource.name in labeled[True] or (
                labeled[False] and
                resource.name not in labeled[False])
        ])
        
    def __str__(self):
        return ("<ResourceCollection: %d resources from %s>"
            % (len(self.resources), " ".join(self.filenames)))
    
    def __repr__(self):
        return str(self)
    
    @property
    def summary(self):
        lines = []
        indentation_boxed = [0]
        def w(s): lines.append(" " * indentation_boxed[0] + s)
        def indent(): indentation_boxed[0] += 2
        def dedent(): indentation_boxed[0] -= 2
        
        w("ResourceCollection: %d resources from %s" % (len(self.resources), " ".join(self.filenames)))
        indent()
        w("Commmon:")
        for (field, value) in self.common.items():
            indent()
            w("%s = %s" % (field.ljust(20), value))
            dedent()
        w("")
        w("Resources:")
        for resource in self.resources:
            indent()
            w(resource.name)
            for (key, value) in sorted(resource.items()):
                if key in ("name", "common"): continue
                indent()
                w("%s = %s" % (key.ljust(20), str(value)))
                dedent()
            dedent()
            w("")
        return "\n".join(lines)
        
