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

import os
import re
import collections
import sys
import json
from future.utils import raise_
import typechecks
from attrdict import AttrMap
from . import util

NEXT_RESOURCE_NUM = 1
class Resource(AttrMap):
    """
    A Resource gives information on how to access some dataset under analysis
    (such as a file), along with any optional metadata meaningful to the user.

    The only required attribute for a resource is `name`. If `name` is not
    specified when the Resource is defined, one is automatically generated.

    The `tags` attribute, if it is specified, is handled slightly specially.
    It is stored using the `Tags` class, which is a Python set that also
    supports a convenient method of membership testing. If `tags` is a `Tags`
    instance, then `tags.foo` returns whether the string "foo" is in the set.
    """
    def __init__(self, name=None, **fields):
        """
        Construct a resource with the specified attributes.

        Parameters
        ----------
        name : string
            Name of the resource. It must be unique to the collection. If it is
            not specified, a unique name is generated.

        **fields : string -> strings, dicts, and lists
            Other fields in the resource.
        """
        global NEXT_RESOURCE_NUM
        if name is not None:
            fields["name"] = name
        if "name" not in fields:
            fields["name"] = "resource-%d" % NEXT_RESOURCE_NUM
            NEXT_RESOURCE_NUM += 1
        fields['tags'] = Tags(fields.get('tags', []))
        AttrMap.__init__(self, fields)
        
    def __str__(self):
        keys = sorted(self.keys())
        util.move_to_front(keys, "name", "tags")
        key_fill = min(30, max(len(x) for x in keys))
        attributes = "\n           ".join(
            "%s = %s" % (
                key.ljust(key_fill),
                " ".join(self.tags) if key == 'tags' else self[key])
            for key in keys)
        return "<Resource: %s >" % attributes

    def __repr__(self):
        return str(self)

    RAISE = object()

    def evaluate(self, expression, error_value=RAISE, extra_bindings={}):
        """
        Evaluate a Python expression or callable in the context of this
        resource.

        Parameters
        ----------
        expression : string or callable
            If a string, then it should give a valid Python expression.
            This expression will be evaluated with the attributes of this
            resource in the local namespace. For example, since the resource
            has a ``name`` attribute, the expression "name.lower()" would
            return the name in lower case. Tags can be accessed through the
            ``tags`` variable. If the resource has a tag called ``foo``, then
            the expression "tags.foo" will evaluate to ``True``. If there is no
            such tag, then "tags.foo" will evaluate to ``False``.

            A few common modules are included in the evaluation namespace,
            including ``os``, ``sys``, ``collections``, ``re``, and ``json``.
            The resource object itself is also available in the ``resource``
            variable.

            As a hack to support a primitive form of exception handling, a
            function called ``on_error`` is also included in the evaluation
            namespace. This function takes a single argument, ``value``, of
            any type and returns None. If ``on_error`` is called while
            evaluating the expression, and the expression subsequently raises
            an exception, then the exception is caught and ``value`` is
            returned as the value of the expression. This means you can write
            expressions like:

                ``on_error(False) or foo.startswith("bar")``

            and if the right side of the expression raises an error (for
            example, if there is no such attribute ``foo`` in the resource),
            then the value ``False`` will be used as the expression's value.
            Note that you must write the expression as it is here: put the
            ``on_error`` clause first, and connect it with the main expression
            with `or` (this ensures that it gets called before the rest of the
            expression).

            If ``expression`` is a callable, then it will be called and passed
            this Resource instance as its argument.

        error_value : object [optional]
            If evaluating the expression results in an uncaught exception,
            the ``error_value`` value will be returned instead. If not
            specified, then ``evaluate`` will raise the exception to the
            caller.

        extra_bindings : dict [optional]
            Additional local variables to include in the evaluation context.

        Returns
        ----------
        The Python object returned by evaluating the expression.

        """
        # Since Python 2 doesn't have a nonlocal keyword, we have to box up the
        # error_value, so we can reassign to it in the ``on_error`` function
        # below.
        error_box = [error_value] 
        try:
            if typechecks.is_string(expression):
                # Give some basic modules.
                environment = dict(STANDARD_EVALUATION_ENVIRONMENT)
                environment["resource"] = self

                # We also add our "on_error" hack.
                def on_error(value):
                    error_box[0] = value
                environment["on_error"] = on_error
                environment.update(extra_bindings)

                return eval(expression, environment, self)
            else:
                return expression(self)                
        except Exception as e:
            if error_box[0] is not Resource.RAISE:
                return error_box[0]
            extra = "Error while evaluating: \n\t%s\non resource:\n%s" % (
                expression, self)
            traceback = sys.exc_info()[2]
            raise_(ValueError, str(e) + "\n" + extra, traceback)
                
    def to_plain_types(self):
        """
        Return this resource represented using Python dicts, lists, and
        strings.
        """
        result = collections.OrderedDict()
        result["tags"] = list(self.tags)
        for (field, value) in self.items():
            if field not in ("name", "tags"):
                result[field] = value
        return result

class Tags(set):
    """
    A set of strings used to group resources.

    This class inherits from Python's `set` class and supports all the
    functionality of that class. Additionally, it supports attribute
    access as a way to test membership: ``tags.foo`` will return ``True`` if
    the string "foo" is in the set, and ``False`` otherwise.
    """
    def __init__(self, tags):
        for tag in tags:
            check_valid_tag(tag)
        set.__init__(self, tags)

    def to_plain_types(self):
        return list(self)

    def __getattr__(self, attribute):
        return attribute in self

    def __repr__(self):
        return "<Tags: %s>" % " ".join(self)

def check_valid_tag(tag):
    """
    Raise an error if the given name is not a valid tag name. Tags must
    be valid Python identifiers and also not builtin methods of the `set`
    class, to avoid ambiguity in using attribute access to test membership
    in the set.
    """
    if tag in vars(Tags):
        raise ValueError(
            "Invalid tag (may not be a method on set objects): '%s'" % tag)
    if re.match('^[\w][\w-]*$', tag) is None:
        raise ValueError("Invalid tag: '%s'" % tag)

STANDARD_EVALUATION_ENVIRONMENT = {
    "os": os,
    "sys": sys,
    "collections": collections,
    "re": re,
    "json": json,
}
