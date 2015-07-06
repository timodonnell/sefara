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

To select all fields, just give the path to the collection:

    sefara-select my_datasets.sefara.py

To get the 'name' and 'path' fields from a resource collection called
"collection.sefara.py":

    sefara-select collection.sefara.py name path

Fields are interpreted as Python expressions and evaluated in a context that
includes the resource's attributes as local variables. For example:

    sefara-select collection.sefara.py "name.lower()" "os.path.abspath(path)"

In csv output, a header row is included by default when more than one field is
selected. To customize the label, give a label of the form "LABEL: EXPRESSION".
For example:

    sefara-select rc.py "resource: name" "full_path: os.path.abspath(path)"

'''

from __future__ import absolute_import, print_function

import argparse
import csv
import sys

from future.utils import raise_

from . import util
from .. import resource
from ..util import shell_quote, move_to_front

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[util.load_collection_parser])
parser.add_argument("field", nargs="*",
    help="Expressions to select from each resource. Specify one or more "
    "times.")
parser.add_argument("--format",
    choices=('csv', 'raw', 'args', 'args-repeated'),
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
    default="raise",
    help="How to handle exceptions raised in expression evaluation. "
    "If 'raise', the script will halt with a traceback. If 'skip', the "
    "problematic resource(s) will be silently omitted from the result. "
    "If 'none', the Python None value will be silently used in place of "
    "the expression. Default: %(default)s.")

def stringify(value):
    if value is None:
        return ''
    if isinstance(value, resource.Tags):
        return " ".join(sorted(value))
    return str(value)

def run(argv=sys.argv[1:]):
    args = parser.parse_args(argv)

    rc = util.load_from_args(args)

    if args.field:
        fields = args.field
    else:
        fields = sorted(rc.attributes)
        move_to_front(fields, "name", "tags")

    fd = open(args.out, "w") if args.out else sys.stdout
    try:
        result = rc.select(*fields, if_error=args.if_error)
        if args.format == "csv":
            writer = csv.writer(fd, lineterminator='\n')
            if (args.header == 'on' or
                    (args.header is None and len(fields) > 1)):
                header = list(result.columns)
                header[0] = "# " + header[0]
                writer.writerow(header)
            for (_, row) in result.iterrows():
                writer.writerow([stringify(x) for x in row])
        elif args.format == "raw":
            for (_, row) in result.iterrows():
                print("".join([stringify(x) for x in row]), file=fd)
        elif args.format == "args":
            for (i, label) in enumerate(result.columns):
                fd.write(" ")
                fd.write(shell_quote("--%s" % label))
                for (_, row) in result.iterrows():
                    fd.write(" ")
                    fd.write(shell_quote(stringify(row[i])))
            fd.write("\n")
        elif args.format == "args-repeated":
            for (_, row) in result.iterrows():
                for (field_name, value) in zip(result.columns, row):
                    fd.write(" ")
                    fd.write(shell_quote("--%s" % field_name))
                    fd.write(" ")
                    fd.write(shell_quote(stringify(value)))
            fd.write("\n")
        else:
            raise ValueError("Unknown format: %s" % format)

    except Exception as e:
        extra = """
        To skip errors like this, pass --if-error skip or --if-error none
        """
        traceback = sys.exc_info()[2]
        raise_(ValueError, str(e) + "\n\n" + extra.strip(), traceback)

    finally:
        fd.close()
