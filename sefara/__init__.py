import re
import json
import collections
from .context import Context

class Resource(Context):
    def __init__(self, name, context, substitutions=True):
        Context.__init__(
            self,
            mapping={"name": name},
            parent=context,
            substitutions=substitutions)

    def __repr__(self):
        key_fill = min(30, max(len(x) for x in self.keys()))
        attributes = "\n           ".join(
            "%s = %s" % (key.ljust(key_fill), value)
            for (key, value) in self.items()) + "\n"
        return "<Resource: %s>" % attributes
   
def load(filename):
    if filename.endswith(".json"):
        with open(filename) as fd:
            data = json.load(fd, object_pairs_hook=collections.OrderedDict)
    else:
        raise ValueError("Unsupported file type: %s" % filename)

    global_context = Context()
    resources = collections.OrderedDict()
    for (key, value) in data.items():
        if key.startswith("@"):
            name = key[1:]
            context = Context(mapping=value, parent=global_context)
            resource = Resource(name, context)
            resources[name] = resource
        elif key.startswith("#"):
            # Ignore comments.
            pass
        else:
            global_context[key] = value

    return ResourceCollection(resources, global_context)

def check_valid_tag(tag):
    if re.match('^[\w][\w-]+$', tag) is None:
        raise ValueError("Invalid tag: %s" % tag)

def label_strings(strings):
    result = {True: set(), False: set()}
    for s in strings:
        if s.startswith("-"):
            result[False].add(s[1:])
        else:
            result[True].add(s)
    return result

def union(*collections):
    result = ResourceCollection()
    for collection in collections:
        result = result.union(collection)
    return result

class ResourceCollection:
    def __init__(self, resources=None, context=None):
        if resources is None:
            resources = []

        if isinstance(resources, list):
            resources = collections.OrderedDict(
                (x.name, x) for x in resources)

        self.resources = collections.OrderedDict()
        for (key, value) in resources.items():
            if value is not None:
                assert value.name == key
                self.resources[key] = value

        self.context = Context() if context is None else context

    def __getitem__(self, index_or_key):
        if isinstance(index_or_key, int):
            return list(self.resources.values())[index_or_key]
        if isinstance(index_or_key, Resource):
            return index_or_key
        return self.resources[index_or_key]

    def __len__(self):
        return len(self.resources)

    def __iter__(self):
        return iter(self.resources.values())

    def singleton(self):
        if len(self.resources) != 1:
            raise ValueError("Expected exactly 1 resource, not %d."
                % len(self.resources))
        return self.resources.values()[0]

    def with_tag(self, *tags):
        labeled = label_strings(tags)
        return ResourceCollection(
            context=self.context,
            resources=[
                resource
                for resource in self
                if any(tag in resource.tags for tag in labeled[True]) or
                   any(tag not in resource.tags for tag in labeled[False])])

        
    def __str__(self):
        if len(self) == 0:
            names = ""
        elif len(self) == 1:
            names = ": %s" % self[0].name
        else:
            names = "\n" + "\n".join(("\t" + x.name) for x in self)         
        return ("<ResourceCollection: %d resources%s>"
            % (len(self.resources), names))

    def __repr__(self):
        return str(self)
    
    @property
    def summary(self):
        lines = []
        indentation_boxed = [0]
        
        def w(s):
            lines.append(" " * indentation_boxed[0] + s)

        def indent():
            indentation_boxed[0] += 2

        def dedent():
            indentation_boxed[0] -= 2
        
        w("ResourceCollection: %d resources from %s" % (len(self.resources), " ".join(self.filenames)))
        indent()
        w("Context:")
        for (field, value) in self.context.items():
            indent()
            w("%s = %s" % (field.ljust(20), value))
            dedent()
        w("")
        w("Resources:")
        for resource in self.resources:
            indent()
            w(resource.name)
            for (key, value) in sorted(resource.items()):
                if key in ("name", "context"):
                    continue
                indent()
                w("%s = %s" % (key.ljust(20), str(value)))
                dedent()
            dedent()
            w("")
        return "\n".join(lines)

def update_tags(existing_tags, new_tags):
    result = set(existing_tags)
    for tag in new_tags:
        if tag.startswith("-"):
            result.discard(tag[1:])
        result.add(tag)
    return result
