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
import json
import sys
import functools
import re
import traceback

import typechecks

from . import util
from ..resource import Tags
from .util import print_stderr as stderr
from ..util import shell_quote, move_to_front

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[util.load_collection_parser])
parser.add_argument("-f", "--field", action="append", nargs="+", default=[],
    help="Field to select. Can be specified multiple times. Interpreted as a "
    "Python expression, so things like 'name.lower()' are valid.")
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

def extract_best(datum):
    if (typechecks.is_string(datum) or
            datum is True or
            datum is False or
            datum is None):
        extractor = "string"
    elif isinstance(datum, (list, Tags)):
        extractor = "joined"
    else:
        extractor = "json"
    return extractors[extractor](datum)

def json_dumps(datum):
    def default(o):
        try:
            return o.to_plain_types()
        except AttributeError:
            return str(o)
    return json.dumps(datum, default=default)

extractors = {
    "best": extract_best,
    "string": lambda x: str(x) if x is not None else '',
    "joined": " ".join,
    "json": json_dumps,
}

def default_field_name(args, expression):
    if args.format == 'args':
        if re.match('^[\w][\w-]*$', expression) is None:
            raise ValueError(
                "Specify an explicit argument name for complex field: '%s'"
                % expression)
        return expression.replace("_", "-")
    return expression

def run(argv=sys.argv[1:]):
    args = parser.parse_args(argv)

    rc = util.load_from_args(args)

    # Tuples of (extractor, name, expression)
    fields = []
    if args.all_fields:
        union_fields = sorted(set.union(*[set(x) for x in rc]))
        move_to_front(union_fields, "name", "tags")
        fields.extend(
            (extractors["best"],
                field,
                functools.partial(
                    lambda field, resource: resource.get(field), field))
            for field in union_fields)
    elif args.field:
        for original_field in args.field:
            field = list(original_field)
            expression = field.pop(0)
            name = (
                default_field_name(args, expression) if not field
                else field.pop(0))
            kind = "best" if not field else field.pop(0)
            if field:
                raise ValueError(
                    "Too many (>3) --field arguments: %s" % original_field)
            try:
                extractor = extractors[kind]
            except KeyError:
                raise ValueError(
                    "Unsupported field kind: %s. Supported kinds: %s" % (
                        kind, " ".join(extractors)))
            fields.append((extractor, name, expression))
    else:
        intersect_fields = sorted(set.union(*[set(x) for x in rc]))
        move_to_front(intersect_fields, "name", "tags")
        stderr(
            "No fields selected. Use the --field argument to specify a field "
            "to select, or --all-fields to select all fields.")
        stderr()
        stderr("Your collection has these fields:\n\t%s"
            % ", ".join(intersect_fields))
        return

    errors = []

    def generate_rows():
        for resource in rc:
            row = []
            for (extractor, name, expression) in fields:
                value = None
                try:
                    value = resource.evaluate(expression)
                except:
                    if args.stop_on_error:
                        raise
                    elif args.skip_errors:
                        break
                    else:
                        errors.append(traceback.format_exc())
                row.append(extractor(value))
            else:
                # Executed if we didn't break above.
                yield row

    field_names = [field_name for (_, field_name, _) in fields]
    fd = open(args.out, "w") if args.out else sys.stdout
    try:
        if args.format == "csv":
            writer = csv.writer(fd)
            if (args.header == 'on' or
                    (args.header is None and len(fields) > 1)):
                header = list(field_names)
                header[0] = "# " + header[0]
                writer.writerow(header)
            for row in generate_rows():
                writer.writerow(row)
        elif args.format == "args":
            rows = list(generate_rows())
            for (i, field_name) in enumerate(field_names):
                fd.write(" ")
                fd.write(shell_quote("--%s" % field_name))
                for row in rows:
                    fd.write(" ")
                    fd.write(shell_quote(row[i]))
            fd.write("\n")
        elif args.format == "args-repeated":
            for row in generate_rows():
                for (field_name, value) in zip(field_names, row):
                    fd.write(" ")
                    fd.write(shell_quote("--%s" % field_name))
                    fd.write(" ")
                    fd.write(shell_quote(value))
            fd.write("\n")
        else:
            raise ValueError("Unknown format: %s" % format)

        if errors:
            stderr("ERRORS (%d)" % len(errors))
            for error in errors:
                stderr()
                stderr(error)
    finally:
        fd.close()

    


