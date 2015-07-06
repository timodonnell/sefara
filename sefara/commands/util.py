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

from __future__ import absolute_import, print_function

import sys
import argparse

from .. import load, hooks

load_collection_parser = argparse.ArgumentParser(add_help=False)
load_collection_parser.add_argument("collection",
    help="Resource collection path or URL. Specify '-' for stdin.")
load_collection_parser.add_argument("-f", "--filter",
    action="append",
    default=[],
    help="Filter expression. Can be specified multiple times; "
    "the result is the intersection of the filters.")
load_collection_parser.add_argument("--transform", action="append", default=[],
    help="Path to Python file with transform function to run. Can be "
    "specified multiple times.")
load_collection_parser.add_argument("--no-environment-transforms",
    dest="environment_transforms",
    action="store_false",
    default=True,
    help="Do not run transforms configured in environment variables.")

def load_from_args(args):
    rc = load(
        args.collection, environment_transforms=args.environment_transforms)
    for value in args.filter:
        rc = rc.filter(value)
    for transform in args.transform:
        hooks.transform(rc, transform)
    return rc

def print_stderr(s=''):
    print(s, file=sys.stderr)
