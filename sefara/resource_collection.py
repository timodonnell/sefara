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
import os

import typechecks

from .util import exec_in_directory, shell_quote
from . import environment

class NoCheckers(Exception):
    pass

class ResourceCollection(object):
    """
    Collection of zero or more resources.

    Resources in a ResourceCollection can be accessed either by name:
        resource_collection["my_dataset"]

    or by index (or slice):
        resource_collection[0]
    """
    def __init__(self, resources, filename="<no file>"):
        """
        Create a new ResourceCollection from a list of resources.

        Parameters
        ----------
        resources : list of `Resource` instances
            Resources.

        filename : string [optional]
            Filename these resources were loaded from. Used in error messages.
        """
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

    def transform_from_environment(self):
        """
        Run the environment-variable-defined transforms on the resources in
        this collection. The transforms will mutate the resources in this
        collection; a new ResourceCollection is NOT returned.

        See the `environment` module for the definition of the environment
        variable used here.
        """
        transforms = os.environ.get(
            environment.TRANSFORM_ENVIRONMENT_VARIABLE, "").split(":")

        for transform in transforms:
            transform = transform.strip()
            if transform:
                self.transform(transform)

    def transform(self, path_or_callable, name='transform', *args, **kwargs):
        """
        Run a function on the resources in this collection. The function is
        expected to mutate the resources in this collection; a new collection
        is NOT returned.

        Parameters
        ----------
        path_or_callable : string or callable
            If string, then this is interpreted as a path to a Python file. The
            file will be exec'd and is expected to define a module attribute
            given by the `name` argument. This attribute will be used as the
            callable. It should take a ResourceCollection instance as an
            argument.

            Otherwise, this parameter should be a callable that takes a
            ResourceCollection instance. It will be invoked on this
            ResourceCollection.

        name : string [optional, default 'transform']
            If `path_or_callable` is a string giving a path to a Python file
            to execute, this parameter gives the attribute in that module to
            use as the callable. Defaults to "transform", i.e. the Python file
            specified by `path_or_callable` is expected to define a function
            called "transform".

        *args, **kwargs
            Additional args and kwargs are passed to the transform function.
        """
        self.run_hook(path_or_callable, name, *args, **kwargs)

    def check(self, checkers=None, include_environment_checkers=True):
        '''
        Run "checkers", either specified directly or using environment
        variables, on this resource collection.

        Checkers are used to validate that the resources in a collection
        meet user-defined criteria, for example, that the paths they point
        to exist.

        Parameters
        ----------
        checkers : list of either callables, strings, or
                    (path, name, args kwargs) tuples [optional]

        include_environment_checkers : boolean [optional, default: True]



        Checkers is a list. Each element can either be a callable, a string
        (path to file), or tuple of (path, name, args, kwargs).

        Each checker should return an iterable of
        # (resource, attempted?, None if no errors otherwise error message )
        '''
        if checkers is None:
            checkers = []

        if include_environment_checkers:
            checkers.extend(
                e.strip()
                for e in os.environ.get(
                    environment.CHECKER_ENVIRONMENT_VARIABLE, "").split(":")
                if e.strip())

        generators = []
        for checker in checkers:
            if isinstance(checker, tuple):
                (path, name, args, kwargs) = checker
                generator = self.run_hook(path, name, *args, **kwargs)
            else:
                generator = self.run_hook(checker, name="check")
            generators.append(generator)

        if not generators:
            raise NoCheckers()

        for row in zip(self, *generators):
            (expected_resource, results) = (row[0], row[1:])
            tuples = []  # (checker, attempted, error)
            for (i, (resource, attempted, error)) in enumerate(results):
                if resource != expected_resource:
                    raise ValueError(
                        "Checker %d (%s): skipping / reordering: %s != %s"
                        % (i, checkers[i], resource, expected_resource))
                tuples.append((str(checkers[i]), attempted, error))
            yield (expected_resource, tuples) 
    
    def run_hook(self, path_or_callable, name, *args, **kwargs):
        """
        Invoke a Python callable (either passed directly or defined in the
        specified Python file) on this ResourceCollection and return the
        result.

        Parameters
        ----------
        path_or_callable : string or callable
            If string, then this is interpreted as a path to a Python file. The
            file will be exec'd and is expected to define a module attribute
            given by the `name` argument. This attribute will be used as the
            callable. It should take a ResourceCollection instance as an
            argument.

            Otherwise, this parameter should be a callable that takes a
            ResourceCollection instance. It will be invoked on this
            ResourceCollection.

        name : string [optional, default 'transform']
            If `path_or_callable` is a string giving a path to a Python file
            to execute, this parameter gives the attribute in that module to
            use as the callable.

        *args, **kwargs
            Additional args and kwargs are passed to the callable after the
            ResourceCollection.
        """
        if hasattr(path_or_callable, '__call__'):
            function = path_or_callable
        else:
            filename = path_or_callable
            defines = exec_in_directory(filename)
            try:
                function = defines[name]
            except KeyError:
                raise AttributeError(
                    "Hook '%s' defines no such field '%s'"
                    % (filename, name))
        return function(self, *args, **kwargs)

    @property
    def tags(self):
        """
        All tags associated with any Resource in this collection.
        """
        result = set()
        for resource in self:
            result.update(resource.tags)
        return result
    
    def filter(self, expression):
        """
        Return a new collection containing only those resources for which
        `expression` evaluated to True.

        Parameters
        ----------
        expression : string or callable
            If a string, then it should give a valid Python expression.
            This expression will be evaluated with the
            attributes of this resource in the local namespace. For
            example, since the resource has a `name` attribute, the
            expression "name.startswith('bar')" is a valid expression.
            Tags can be accessed through the `tags` variable.
            If the resource has a tag called `foo`, then the expression
            "tags.foo" will evaluate to True. If there is no such tag,
            then "tags.foo" will evaluate to False.

            If a callable, then it will be called and passed this Resource
            instance as its argument.

        Returns
        ----------
        A new ResourceCollection containing those resources for which
        `expression` evaluated to True.        
        """
        return ResourceCollection([
            x for x in self
            if x.evaluate(expression)
        ], self.filename)

    def singleton(self, raise_on_multiple=True):
        """
        If this ResourceCollection contains exactly 1 resource, return it.
        Otherwise, raise a ValueError.
        """
        if len(self) == 0 or (raise_on_multiple and len(self) > 1):
            raise ValueError("Expected exactly 1 resource, not %d: %s."
                % (len(self.resources), ' '.join(self.resources)))
        return self[0]

    def __getitem__(self, index_or_key):
        if isinstance(index_or_key, (int, slice)):
            return list(self.resources.values())[index_or_key]
        try:
            result = self.resources[index_or_key]
            if result.name != index_or_key:
                raise KeyError
            return result
        except KeyError:
            # Rebuild dictionary since names may have changed.
            self.resources = collections.OrderedDict(
                (x.name, x) for x in self)
            return self.resources[index_or_key]

    def __len__(self):
        return len(self.resources)

    def __iter__(self):
        return iter(self.resources.values())

    def to_plain_types(self):
        """
        Return a representation of this collection using Python dicts, lists,
        and strings.
        """
        result = collections.OrderedDict()
        for resource in self:
            result[resource.name] = resource.to_plain_types()
        return result

    def to_json(self, indent=4):
        """
        Return a string giving this collection represented as JSON.
        """
        return json.dumps(self.to_plain_types(), indent=indent)

    def to_python(self, indent=4):
        """
        Return a string giving this collection represented as Python code.
        """
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

    def write(self, file=None, format=None, indent=None):
        """
        Serialize this collection to disk.

        Parameters
        ----------
        file : string or file handle [optional, default: sys.stdout]
            Path or file handle to write to.

        format : string, one of "python" or "json" [optional]
            Output format. If not specified, it is guessed from the filename
            extension.

        indent : int [optional]
            Number of spaces to use for indentation.
        """
        close_on_exit = False
        if typechecks.is_string(file):
            fd = open(file, "w")
            close_on_exit = True
            if format is None:
                if file.endswith(".json"):
                    format = "json"
                elif file.endswith(".py"):
                    format = "python"
                else:
                    raise ValueError(
                        "Couldn't guess format from filename: %s" % file)
        elif not file:
            fd = sys.stdout
            if format is None:
                format = "json"
        else:
            fd = file
        try:
            extra_args = {} if indent is None else {"indent": indent}
            if format == "json":
                value = self.to_json(**extra_args)
            elif format == "python":
                value = self.to_python(**extra_args)
            else:
                raise ValueError("Unsupported format: %s" % format)
            fd.write(value)
        finally:
            if close_on_exit:
                fd.close()

    @property
    def summary(self):
        """
        Return a string summarzing the resources in this collection, including
        their attributes.
        """
        lines = []

        def w(s=""):
            lines.append(s)
        
        w("ResourceCollection: %d resources from %s" %
            (len(self), self.filename))
        for resource in self:
            w(str(resource))
            w()
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