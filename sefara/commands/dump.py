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
'''

from __future__ import absolute_import, print_function

import argparse
import sys

from . import util

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[util.load_collection_parser])
parser.add_argument("--format", choices=('json', 'python'),
    help="Output format")
parser.add_argument("--out",
    help="Output file. Default: stdout.")
parser.add_argument("--indent", type=int, default=4,
    help="Number of spaces for indentation in output. Default: %(default)d.")

def run(argv=sys.argv[1:]):
    args = parser.parse_args(argv)
    rc = util.load_from_args(args)
    rc.write(args.out, args.format, indent=args.indent)
