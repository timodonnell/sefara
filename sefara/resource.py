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

import re
import collections

from attrdict import AttrMap

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
        key_fill = min(30, max(len(x) for x in self.keys()))
        attributes = "\n           ".join(
            "%s = %s" % (key.ljust(key_fill), value)
            for (key, value) in self.items()) + "\n"
        return "<Resource: %s>" % attributes

    def __repr__(self):
        return str(self)

    def matches(self, expression):
        return eval(expression, {}, self)

    def to_dict(self):
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

    def __getattr__(self, attribute):
        return attribute in self

    def __repr__(self):
        return "<Tags: %s>" % " ".join(self)

def check_valid_tag(tag):
    if tag in vars(set):
        raise ValueError(
            "Invalid tag (may not be a method on set objects): '%s'" % tag)
    if re.match('^[\w][\w-]*$', tag) is None:
        raise ValueError("Invalid tag: '%s'" % tag)
