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
Select fields from a sefara dataset.
'''

from __future__ import absolute_import, print_function

import argparse
import csv
import json
import sys
import functools
import re

try:  # py3
    from shlex import quote
except ImportError:  # py2
    from pipes import quote

import typechecks

from . import util
from ..resource import Tags

parser = argparse.ArgumentParser(usage=__doc__)
util.add_load_arguments(parser)
parser.add_argument("--field", action="append", nargs="+", default=[])
parser.add_argument("--format", choices=('csv', 'args'), default="csv")
parser.add_argument("--header", choices=('on', 'off'))
parser.add_argument("--out")
parser.add_argument("--all-fields", action="store_true", default=False)

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
    return json.dumps(datum, default=list)

extractors = {
    "best": extract_best,
    "string": lambda x: str(x) if x is not None else '',
    "joined": " ".join,
    "json":
        lambda datum: json.dumps(datum, default=lambda o: o.to_plain_types()),
}

def move_to_front(lst, *items):
    for item in reversed(items):
        if item in lst:
            lst.remove(item)
            lst.insert(0, item)

def stderr(s=''):
    print(s, file=sys.stderr)

def default_field_name(args, expression):
    if args.format == 'args':
        if re.match('^[\w][\w-]*$', expression) is None:
            raise ValueError(
                "Specify an explicit argument name for complex field: '%s'"
                % expression)
        return expression.replace("_", "-")
    return expression

def run():
    args = parser.parse_args()

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
            expression = field.pop(-1)
            name = (
                default_field_name(args, expression) if not field
                else field.pop(-1))
            kind = "best" if not field else field.pop(-1)
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
        stderr("Fields found in all resources in your collection:\n\t%s"
            % ", ".join(intersect_fields))
        return

    def generate_rows():
        for resource in rc:
            row = []
            for (extractor, name, expression) in fields:
                value = resource.evaluate(expression)
                row.append(extractor(value))
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
            for row in generate_rows():
                for (field_name, value) in zip(field_names, row):
                    fd.write(" ")
                    fd.write(quote("--%s" % field_name))
                    fd.write(" ")
                    fd.write(quote(value))
        else:
            raise ValueError("Unknown format: %s" % format)
    finally:
        fd.close()

