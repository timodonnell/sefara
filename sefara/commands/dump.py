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
'''
Dump a sefara dataset, possibly into a different format or after applying
filters or decorators.
'''

from __future__ import absolute_import, print_function

import argparse
import sys

from . import util

parser = argparse.ArgumentParser(usage=__doc__)
util.add_load_arguments(parser)
parser.add_argument("--format", choices=('json', 'python'), default="json")
parser.add_argument("--out")

def run():
    args = parser.parse_args()
    rc = util.load_from_args(args)
    fd = open(args.out, "w") if args.out else sys.stdout
    try:
        if args.format == "python":
            raise NotImplementedError()
        elif args.format == "json":
            print(rc.to_json(), file=fd)
        else:
            raise ValueError("Unknown format: %s" % format)
    finally:
        fd.close()
