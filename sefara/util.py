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
A few utility functions and imports.
"""

from __future__ import absolute_import

import os

try:  # py3
    from shlex import quote as shell_quote
except ImportError:  # py2
    from pipes import quote as shell_quote

try:
    # Python 2
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    # Python 2
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

try:
    from urllib2 import urlopen  # py 2
except ImportError:
    from urllib.request import urlopen  # py 3

def exec_in_directory(filename=None, code=None):
    """
    Execute Python code from either a file or passed as an argument. If a file
    is specified, the code will be executed with the current working directory
    set to the directory where the file resides.

    If both ``filename`` and ``code`` are specified, then ``code`` is executed,
    but ``filename`` is used to set the current working directory, and in error
    messages.

    Parameters
    ----------
    filename : string [optional]
        Path to file with Python code to execute.

    code : string [optional]
        Python code to execute

    Returns
    ----------
    dict giving module-level attributes defined by the executed code

    """
    old_cwd = None
    directory = os.path.dirname(filename) if filename else None
    if code is None:
        with open(filename) as fd:
            code = fd.read()
    compiled = compile(code, filename if filename else '<none>', 'exec')
    result = {}
    try:
        if directory:
            old_cwd = os.getcwd()
            os.chdir(directory)
        exec(compiled, result)
    finally:
        if directory:
            os.chdir(old_cwd)
    return result

def move_to_front(lst, *items):
    """
    Move the specified items to the front of the given list. If an item is not
    in the list, it is ignored.

    Mutates the list. Does not return anything.
    """ 
    for item in reversed(items):
        if item in lst:
            lst.remove(item)
            lst.insert(0, item)