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
    from urllib2 import urlopen  # py 2
except ImportError:
    from urllib.request import urlopen  # py 3

def exec_in_directory(filename=None, code=None):
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
    for item in reversed(items):
        if item in lst:
            lst.remove(item)
            lst.insert(0, item)