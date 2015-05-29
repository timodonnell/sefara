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

import collections
import json
import os
import contextlib
try:
    # Python 2
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from .resource_collection import ResourceCollection
from .resource import Resource
from .util import exec_in_directory, urlparse, urlopen
from . import export

def load(filename, filters=None, transforms=None, environment_transforms=None):
    parsed = urlparse(filename)

    # Parse operations (filters and transforms) from the URL fragment
    # (everything after the '#')
    # Operations is a list of (op [either 'filter' or 'transform'], value))
    operations = []
    fragment = parse_qsl(parsed.fragment)
    data_format = None
    for (key, value) in fragment:
        key = key.lower()
        if key == 'filter' or key == 'transform':
            operations.append((key, value))
        elif key == 'format':
            data_format = value
        elif key == 'environment_transforms':
            value = value.lower()
            if environment_transforms is None:
                # If environment_transforms is given as an argument to this
                # function, than that value overrides.
                if value == "true":
                    environment_transforms = True
                elif value == "false":
                    environment_transforms = False
                else:
                    raise ValueError(
                        "Expected environment_transforms to be 'true' or "
                        "'false, not: %s" % value)
        else:
            raise ValueError("Unsupported operation: %s" % key)

    # Add filters and transforms specified in the arguments after anything
    # parsed from the URL.
    if filters:
        operations.extend(("filter", x) for x in filters)
    if transforms:
        operations.extend(("transform", x) for x in filters)

    # Default scheme is 'file', and needs an absolute path.
    absolute_local_filename = None
    if not parsed.scheme or parsed.scheme.lower() == 'file':
        absolute_local_filename = os.path.abspath(parsed.path)
        parsed = parsed._replace(
            scheme="file",
            path=absolute_local_filename)
        filename = parsed.geturl()

    # Guess data format from filename extension if not specified.
    if data_format is None:
        if parsed.path.endswith(".py"):
            data_format = "python"
        elif parsed.path.endswith(".json"):
            data_format = "json"
        else:
            raise ValueError("Couldn't guess format: %s" % filename)

    with contextlib.closing(urlopen(filename)) as fd:
        # We don't apply environment_transforms here as we will apply them
        # ourselves after any other specified transforms or filters.    
        rc = loads(
            fd.read(),
            filename=absolute_local_filename,
            format=data_format,
            environment_transforms=False)

    # Apply filters and transforms.
    for (operation, value) in operations:
        if operation == 'filter':
            rc = rc.filter(value)
        elif operation == 'transform':
            rc.transform(value)
        else:
            assert(False)

    if environment_transforms is not False:
        rc.transform_from_environment()

    return rc

def loads(data, filename=None, format="json", environment_transforms=True):
    rc = None
    transforms = []
    if format == "python":
        try:
            old_resources = export._EXPORTED_RESOURCES
            old_transforms = export._TRANSFORMS
            export._EXPORTED_RESOURCES = []
            export._TRANSFORMS = []
            exec_in_directory(filename=filename, code=data)
        finally:
            transforms = export._TRANSFORMS
            resources = export._EXPORTED_RESOURCES
            export._EXPORTED_RESOURCES = old_resources
            export._TRANSFORMS = old_transforms
        rc = ResourceCollection(resources, filename)
    elif format == "json":
        parsed = json.loads(data, object_pairs_hook=collections.OrderedDict)
        with_comments_removed = remove_keys_starting_with_hash(parsed)
        resources = [
            Resource(name=key, **value)
            for (key, value) in with_comments_removed.items()
        ]
        rc = ResourceCollection(resources, filename)
    else:
        raise ValueError("Unsupported file format: %s" % filename)

    for transform in transforms:
        rc.transform(transform)

    if environment_transforms:
        rc.transform_from_environment()

    return rc

def remove_keys_starting_with_hash(obj):
    if isinstance(obj, dict):
        return collections.OrderedDict(
            (key, remove_keys_starting_with_hash(value))
            for (key, value) in obj.items()
            if not key.startswith("#"))
    return obj