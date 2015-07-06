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
Read and then write a sefara resource collection, possibly into a different
format or after applying filters or transforms.

As an experimental feature, the resources can be mutated with Python code
specified with the --code argument. For example:

    sefara-dump data.py --code 'name = name.upper()'

would capitalize all the resource names. Multiple code arguments can be given,
and any new variables defined become attributes of the resources:

    sefara-dump data.py --code 'upper_name = name.upper()' 'lower_name = name.lower()'

This would add two new attributes to each resource, upper_name and lower_name. 
Note that the input file is never modified. The --code argument only affects
the output.
'''

from __future__ import absolute_import, print_function

import argparse
import sys
import six

from . import util
from .. import resource

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[util.load_collection_parser])
parser.add_argument("--format", choices=('python', 'json'),
    help="Output format")
parser.add_argument("--out",
    help="Output file. Default: stdout.")
parser.add_argument("--indent", type=int, default=4,
    help="Number of spaces for indentation in output. Default: %(default)d.")
parser.add_argument("--code", nargs="+",
    help="Code to run in the context of each resource. Any new varialbes "
    "defined become attributes of each resource. Any number of arguments "
    "may be specified, each giving one line of code.")

def run(argv=sys.argv[1:]):
    args = parser.parse_args(argv)
    rc = util.load_from_args(args)

    if args.code:
        code = "\n".join(args.code)
        environment = dict(resource.STANDARD_EVALUATION_ENVIRONMENT)
        for r in rc:
            environment["resource"] = r
            six.exec_(code, environment, r)

    rc.write(args.out, args.format, indent=args.indent)
