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
import pandas
import re

import typechecks

from . import util
from . import Resource

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

    @property
    def tags(self):
        """
        The tags associated with any resources in this collection.
        """
        result = set()
        for resource in self:
            result.update(resource.tags)
        return result

    @property
    def attributes(self):
        """
        The attribute names used by resouces in this collection.
        """
        result = set()
        for resource in self:
            result.update(resource)
        return result

    def filter(self, expression):
        """
        Return a new collection containing only those resources for which
        ``expression`` evaluated to True.

        Parameters
        ----------
        expression : string or callable
            If a string, then it should give a valid Python expression.
            This expression will be evaluated with the
            attributes of this resource in the local namespace. For
            example, since the resource has a ``name`` attribute, the
            expression "name.startswith('bar')" is a valid expression.
            Tags can be accessed through the ``tags`` variable.
            If the resource has a tag called ``foo``, then the expression
            "tags.foo" will evaluate to True. If there is no such tag,
            then "tags.foo" will evaluate to False.

            If a callable, then it will be called and passed this `Resource`
            instance as its argument.

        Returns
        ----------
        A new ResourceCollection containing those resources for which
        `expression` evaluated to True.        
        """
        extra_bindings = {key: None for key in self.attributes}
        return ResourceCollection([
            x for x in self
            if x.evaluate(expression, extra_bindings=extra_bindings)
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

    def select_series(self, expression):
        """
        Select a single field as a pandas series.

        See `select`.
        """
        return self.select(('value', expression))['value']

    def select(self, *expressions, **kwargs):
        """
        Select fields (or expressions) from each resource as a pandas
        DataFrame.

        Parameters
        ----------
        *expressions : string, callable, or (string, string or callable) pair
            One or more expressions giving the fields to select.

            Each expression can be either a ``string`` expression, a
            ``callable``, or a ``(string, string or callable)`` pair giving a
            label and an expression.

            Labels give the column names in the result. Labels can be specified
            either by giving a ``(label, expression)`` pair, or giving a string
            of the form "LABEL: EXPRESSION", such as
            "upper_name: name.upper()". Here "upper_name" is the label, and
            "name.upper()" is the expression that will be evaluated. If not
            specified, labels default to the text of the ``expression`` if
            ``expression`` is a string, and an automatically generated label if
            ``expression`` is a callable.

            Each ``expression`` will be passed to `Resource.evaluate` for each
            resource in the collection. See that method's docs for details on
            expression evaluation.

        if_error : string, one of "raise", "skip", or "none" [default: "raise"]
            Must be specified as a keyword argument. Controls the behavior when
            evaluation of an expression raises an uncaught exception. One of:

            raise
                Raise the exception to the caller. This is the default.

            skip
                Skip resources where evaluation of any of the expressions
                raises an error. These resources will be omitted from the
                result.

            none
                If evaluating an expression on a resource raises an exception,
                set that entry in the result to ``None``.

        Returns
        -------
        A `pandas.DataFrame`. Rows correspond to resources. Columns correspond
        to the specified expressions.
        """
        if_error = kwargs.pop("if_error", "raise")
        if if_error == "raise" or if_error == "skip":
            error_value = Resource.RAISE
        elif if_error == "none":
            error_value = None
        else:
            raise TypeError("if_error should be 'raise', 'skip', or 'none'")
        if kwargs:
            raise TypeError("Invalid keyword arguments: %s" % " ".join(kwargs))

        labels_and_expressions = []
        expr_num = 1
        for expression in expressions:
            if isinstance(expression, tuple):
                (label, expression) = expression
            elif typechecks.is_string(expression):
                match = re.match(r"^([\w ]+):(.*)$", expression)
                if match is None:
                    label = expression
                else:
                    (label, expression) = match.groups()
            else:
                label = "expr_%d" % expr_num
                expr_num += 1
            labels_and_expressions.append((label, expression))

        df_dict = collections.OrderedDict(
            (label, []) for (label, _) in labels_and_expressions)

        extra_bindings = {key: None for key in self.attributes}

        def values_for_resource(resource):
            result = []
            for (label, expression) in labels_and_expressions:
                try:
                    value = resource.evaluate(
                        expression,
                        error_value=error_value,
                        extra_bindings=extra_bindings)
                except:
                    if if_error == "raise":
                        raise
                    elif if_error == "skip":
                        return None
                    elif if_error == "none":
                        value = None
                result.append(value)
            return result

        for resource in self:
            row = values_for_resource(resource)
            if row is not None:
                for ((label, _), value) in zip(labels_and_expressions, row):
                    df_dict[label].append(value)

        return pandas.DataFrame(df_dict)

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
        w("# " + " ".join(util.shell_quote(x) for x in sys.argv))
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
                format = "python"
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
        A string summarzing the resources in this collection, including their
        attributes.
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