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

try:
    from exceptions import AttributeError
except ImportError:
    pass

from attrdict import AttrMap

from . import util

NEXT_RESOURCE_NUM = 1
class Resource(AttrMap):
    def __init__(self, name=None, **fields):
        global NEXT_RESOURCE_NUM
        if name is not None:
            fields["name"] = name
        if "name" not in fields:
            fields["name"] = "resource-%d" % NEXT_RESOURCE_NUM
            NEXT_RESOURCE_NUM += 1
        fields['tags'] = Tags(fields.get('tags', []))
        AttrMap.__init__(self, fields)
        
    def __str__(self):
        keys = list(self.keys())
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

    def evaluate(self, expression):
        try:
            try:
                return expression(self)
            except TypeError:
                # Give some basic modules.
                environment = {
                    "resource": self,
                    "os": os,
                    "sys": sys,
                    "collections": collections,
                    "re": re,
                }
                return eval(expression, environment, self)
        except Exception as e:
            # See http://stackoverflow.com/questions/6062576/adding-information-to-a-python-exception
            extra = "\nWhile evaluating: \n\t%s\non resource:\n%s" % (
                expression, self)
            try:
                # Python 3
                raise(type(e)(str(e) + extra).with_traceback(sys.exc_info()[2]))
            except AttributeError:
                raise(type(e), type(e)(e.message + extra), sys.exc_info()[2])
                
    def to_plain_types(self):
        result = collections.OrderedDict()
        result["tags"] = list(self.tags)
        for (field, value) in self.items():
            if field not in ("name", "tags"):
                result[field] = value
        return result

class Tags(set):
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
    if tag in vars(Tags):
        raise ValueError(
            "Invalid tag (may not be a method on set objects): '%s'" % tag)
    if re.match('^[\w][\w-]*$', tag) is None:
        raise ValueError("Invalid tag: '%s'" % tag)
