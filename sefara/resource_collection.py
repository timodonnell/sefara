# Copyright (c) 2015. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import sys
import json
import collections
import datetime
import getpass

from .util import exec_in_directory, shell_quote

class ResourceCollection(object):
    def __init__(self, resources, filename="<no file>"):
        if isinstance(resources, list):
            resources = collections.OrderedDict(
                (x.name, x) for x in resources)
        self.resources = collections.OrderedDict()
        for (key, value) in resources.items():
            if value is not None:
                assert value.name == key
                self.resources[key] = value
        self.resources = resources
        self.filename = filename

    def transform(self, filename_or_callable, name='default'):
        if hasattr(filename_or_callable, '__call__'):
            filename_or_callable(self)
        else:
            filename = filename_or_callable
            defines = exec_in_directory(filename)
            function = defines.get(name)
            if function is None:
                raise AttributeError(
                    "Decorator '%s' defines no such field '%s'"
                    % (filename, name))
            function(self)

    @property
    def tags(self):
        result = set()
        for resource in self:
            result.update(resource.tags)
        return result
    
    def filter(self, expression):
        return ResourceCollection([
            x for x in self
            if x.evaluate(expression)
        ], self.filename)

    def singleton(self):
        if len(self.resources) != 1:
            raise ValueError("Expected exactly 1 resource, not %d."
                % len(self.resources))
        return self[0]

    def __getitem__(self, index_or_key):
        if isinstance(index_or_key, int):
            return list(self.resources.values())[index_or_key]
        return self.resources[index_or_key]

    def __len__(self):
        return len(self.resources)

    def __iter__(self):
        return iter(self.resources.values())

    def to_plain_types(self):
        result = collections.OrderedDict()
        for resource in self:
            result[resource.name] = resource.to_plain_types()
        return result

    def to_json(self, indent=4):
        return json.dumps(self.to_plain_types(), indent=indent)

    def to_python(self, indent=4):
        lines = []

        def w(s=''):
            lines.append(s)

        w("# Generated on %s by %s with the command:"
            % (datetime.datetime.now(), getpass.getuser()))
        w("# " + " ".join(shell_quote(x) for x in sys.argv))
        w()
        w("from sefara import export")
        w()
        spaces = " " * indent
        for resource in self:
            w("export(")
            w(spaces + "name=%s," % json.dumps(resource.name))
            plain_types = resource.to_plain_types()
            w(spaces + "tags=%s," % json.dumps(plain_types.pop('tags', [])))
            for (key, value) in plain_types.items():
                json_value = json.dumps(value, indent=indent)
                indented = json_value.replace("\n", "\n" + spaces)
                w(spaces + "%s=%s," % (key, indented))
            lines[-1] = lines[-1][:-1] + ")"  # Drop last comma and close paren
            w()
        return "\n".join(lines)

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
        
        w("ResourceCollection: %d resources from %s" %
            (len(self), self.filename))
        indent()
        w("Context:")
        for (field, value) in self.context.items():
            indent()
            w("%s = %s" % (field.ljust(20), value))
            dedent()
        w("")
        w("Resources:")
        for resource in self:
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

    def __str__(self):
        if len(self) == 0:
            names = ""
        elif len(self) == 1:
            names = ": %s" % self[0].name
        else:
            names = "\n" + "\n".join(("\t" + x.name) for x in self)         
        return ("<ResourceCollection: %d resources%s>"
            % (len(self), names))

    def __eq__(self, other):
        return (isinstance(other, ResourceCollection)
            and self.resources == other.resources)

    def __repr__(self):
        return str(self)