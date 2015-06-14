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
Select fields from a sefara collection.
'''

from __future__ import absolute_import, print_function

import argparse
import csv
import sys

from . import util
from .util import print_stderr as stderr
from ..util import shell_quote, move_to_front

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[util.load_collection_parser])

parser.add_argument("field", nargs="*",
    help="Field(s) to select. Can be specified multiple times. Interpreted as "
    "a Python expression, so things like 'name.lower()' are valid.")
parser.add_argument("--format", choices=('csv', 'args', 'args-repeated'),
    default="csv",
    help="Output format. Default: %(default)s.")
parser.add_argument("--header", choices=('on', 'off'),
    help="Whether to output a header row in csv format. Defaults to 'on' if "
    "more than one field is selected, 'off' otherwise.")
parser.add_argument("--out", help="Output file. Default: stdout.")
parser.add_argument("--all-fields", action="store_true", default=False,
    help="Select all fields")
parser.add_argument("--stop-on-error", action="store_true", default=False,
    help="If an error occurs processing a resource, quit. By default, the "
    "problematic field is set to None, and any errors are printed at the "
    "end.")
parser.add_argument("--skip-errors", action="store_true", default=False,
    help="If an error occurs processing a resource, silently skip that "
    "resource.")
parser.add_argument("--if-error",
    choices=("raise", "skip", "none"),
        default="raise")

def run(argv=sys.argv[1:]):
    args = parser.parse_args(argv)

    rc = util.load_from_args(args)

    if args.all_fields:
        fields = sorted(set.union(*[set(x) for x in rc]))
        move_to_front(fields, "name", "tags")
    else:
        fields = args.field
    
    if not fields:
        intersect_fields = sorted(set.union(*[set(x) for x in rc]))
        move_to_front(intersect_fields, "name", "tags")
        stderr(
            "No fields selected. Use --all-fields to select all fields.")
        stderr()
        stderr("Your collection has these fields:\n\t%s"
            % ", ".join(intersect_fields))
        return

    result = rc.select(*fields, if_error=args.if_error)
    fd = open(args.out, "w") if args.out else sys.stdout
    try:
        if args.format == "csv":
            writer = csv.writer(fd)
            if (args.header == 'on' or
                    (args.header is None and len(fields) > 1)):
                header = list(result.columns)
                header[0] = "# " + header[0]
                writer.writerow(header)
            for (_, row) in result.iterrows():
                writer.writerow([str(x) for x in row])
        elif args.format == "args":
            for (i, label) in enumerate(result.columns):
                fd.write(" ")
                fd.write(shell_quote("--%s" % label))
                for (_, row) in result.iterrows():
                    fd.write(" ")
                    fd.write(shell_quote(str(row[i])))
            fd.write("\n")
        elif args.format == "args-repeated":
            for (_, row) in result.iterrows():
                for (field_name, value) in zip(result.columns, row):
                    fd.write(" ")
                    fd.write(shell_quote("--%s" % field_name))
                    fd.write(" ")
                    fd.write(shell_quote(str(value)))
            fd.write("\n")
        else:
            raise ValueError("Unknown format: %s" % format)

    finally:
        fd.close()
