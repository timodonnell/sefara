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

"""
Instantiate ResourceCollection instances from files or strings.
"""

from __future__ import absolute_import

import collections
import json
import os
import sys
import re

from . import resource_collection
from . import resource
from . import util
from . import exporting
from . import hooks

def load(
        filename,
        format=None,
        filters=None,
        transforms=None,
        environment_transforms=None):

    """
    Load a `ResourceCollection` from a file or URL.

    Collections can be defined using either Python or JSON.

    Parameters
    ----------
    filename : string
        Path or URL to resource collection. If a path is given, it is
        equivalent to a "file://<path>" URL. Supports any protocol handled by
        `urlopen`, such as HTTP and HTTPS.

        Can be the string '-' to read from stdin. 

        May include a "fragment", the part of a URL following a "#" symbol,
        e.g. "file1.py#filter=tags.foo". The fragment is a query string of
        key/value pairs separated by "&" symbols, e.g.
        "file1.txt#filter=tags.foo&format=json".

        Valid fragment keys are:

            filter
                The value is a Python expression giving a sefara filter.

            transform
                The value is a path to a Python file with a sefara transform.

            format
                The value gives the format of the data, either "python" or
                "json".

            environment_transforms
                The value should be "true" or "false" indicating whether to run
                transforms configured with environment variables.

        The fragment operations are processed in order, left to right, and
        can be specified multiple times. That is, the URL:

            ``file.py#filter=tags.bar&filter=tags.baz``
        
        is equivalent to:
        
            ``file.py#filter=tags.bar and tags.baz``

        Fragment values can have spaces, and should not be quoted even if they
        do (as in the above example).

    format : "python" or "json" [optional]
        Format of data. Overrides any setting specified in the filename URL. If
        it is not specified in either place, it is guessed from the filename
        extension.

    filters : list of strings or callbles [optional]
        Filters to run on the ResourceCollection, in addition to any
        specified in the filename. Anything you can pass to
        `ResourceCollection.filter` is accepted.

    transforms : list of strings [optional]
        Transforms to run on the ResourceCollection, in addition to any
        specified in the filename or from the environment. Anything you
        you can pass to `hooks.transform` is accepted.

    environment_transforms : Boolean [optional]
        Whether to run environment_transforms. If specified, this will override
        the "environment_transforms" fragment setting specified in the filename
        URL. If not specified in either place, the default is True.

    Returns
    ----------
    ``ResourceCollection`` instance.

    """
    parsed = util.urlparse(filename)

    # Parse operations (filters and transforms) from the URL fragment
    # (everything after the '#')
    # Operations is a list of (op [either 'filter' or 'transform'], value))
    operations = []
    try:
        if parsed.fragment:
            # If our fragment begins with an '&' symbol, we ignore it. 
            unparsed_fragment = parsed.fragment
            if unparsed_fragment.startswith("&"):
                unparsed_fragment = unparsed_fragment[1:]
            fragment = util.parse_qsl(unparsed_fragment, strict_parsing=True)
        else:
            fragment = []
    except ValueError as e:
        raise ValueError("Couldn't parse fragment '%s': %s" % (
            parsed.fragment, e))
    for (key, value) in fragment:
        key = key.lower()
        if key == 'filter' or key == 'transform':
            operations.append((key, value))
        elif key == 'format':
            if format is None:
                format = value
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
    fd = None
    absolute_local_filename = None
    if not parsed.scheme or parsed.scheme.lower() == 'file':
        if parsed.path == '-':
            # Read from stdin.
            fd = sys.stdin
        else:
            absolute_local_filename = os.path.abspath(parsed.path)
            parsed = parsed._replace(
                scheme="file",
                fragment="",
                path=absolute_local_filename)
            filename = parsed.geturl()

    # Try to guess data format from filename extension if not specified.
    if format is None:
        if parsed.path.endswith(".py"):
            format = "python"
        elif parsed.path.endswith(".json"):
            format = "json"

    try:
        if fd is None:
            fd = util.urlopen(filename)

        # We don't apply environment_transforms here as we will apply them
        # ourselves after any other specified transforms or filters.    
        rc = loads(
            fd.read(),
            filename=absolute_local_filename,
            format=format,
            environment_transforms=False)
    finally:
        if fd is not None and fd is not sys.stdin:
            fd.close()        

    # Apply filters and transforms.
    for (operation, value) in operations:
        if operation == 'filter':
            rc = rc.filter(value)
        elif operation == 'transform':
            hooks.transform(rc, value)
        else:
            assert(False)

    if environment_transforms is not False:
        hooks.transform_from_environment(rc)

    return rc

def loads(data, filename=None, format=None, environment_transforms=True):
    """
    Load a ResourceCollection from a string.

    Parameters
    ----------
    data : string
        ResourceCollection specification in either Python or JSON.

    filename : string [optional]
        filename where this data originally came from to use in error messages

    format : string,  either "python" or "json" [default: guess from data]
        format of the data

    environment_transforms : Boolean [default: True]
        whether to run transforms configured in environment variables.

    Returns
    -------
    ResourceCollection instance.
    """
    if format is None:
        # Attempt to guess format from data.
        # We call it JSON if the first non whitespace character is '{',
        # otherwise Python.
        format = "json" if re.match(r"^\W*{", data) else "python"

    rc = None
    transforms = []
    if format == "python":
        try:
            old_resources = exporting._EXPORTED_RESOURCES
            old_transforms = exporting._TRANSFORMS
            exporting._EXPORTED_RESOURCES = []
            exporting._TRANSFORMS = []
            util.exec_in_directory(filename=filename, code=data)
        finally:
            transforms = exporting._TRANSFORMS
            resources = exporting._EXPORTED_RESOURCES
            exporting._EXPORTED_RESOURCES = old_resources
            exporting._TRANSFORMS = old_transforms
        rc = resource_collection.ResourceCollection(resources, filename)
    elif format == "json":
        parsed = json.loads(data, object_pairs_hook=collections.OrderedDict)
        resources = [
            resource.Resource(name=key, **value)
            for (key, value) in parsed.items()
        ]
        rc = resource_collection.ResourceCollection(resources, filename)
    else:
        raise ValueError("Unsupported file format: %s" % filename)

    for transform in transforms:
        hooks.transform(rc, transform)

    if environment_transforms:
        hooks.transform_from_environment(rc)
    return rc
