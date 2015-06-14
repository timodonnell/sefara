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
Validate a sefara resource collection and report the results.

Routines for validating resources are called "checkers", and are usually
specified in the SEFARA_CHECKER environment variable. Additional checkers may
be specified with the --checker argument to this script.
'''

from __future__ import absolute_import, print_function

import argparse
import sys
import textwrap

from . import util
from .. import resource_collection, hooks
from .util import print_stderr as stderr

parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[util.load_collection_parser])
parser.add_argument("--checker", action="append", default=[],
    help="Path to checker to run. Can be specified multiple times.")
parser.add_argument(
    "--no-environment-checkers",
    dest="environment_checkers",
    action="store_false",
    default=True,
    help="Run only the checkers explicitly specified. Do not run checkers "
    "configured in environment variables.")
parser.add_argument("-v", "--verbose", action="store_true", default=False)
parser.add_argument("-q", "--quiet", action="store_true", default=False,
    help="Print only a summary of errors.")
parser.add_argument("--width", type=int, default=100,
    help="Line width. Default: %(default)d.")

def run(argv=sys.argv[1:]):
    args = parser.parse_args(argv)
    rc = util.load_from_args(args)

    results = hooks.check(
        rc,
        args.checker,
        include_environment_checkers=args.environment_checkers)

    try:
        problematic_resources = []
        for (i, (resource, tpls)) in enumerate(results):
            if i == 0:
                print("Checkers:")
                for (checker_num, (checker, _, _)) in enumerate(tpls):
                    print("\t[%d]\t%s" % (checker_num, checker))
                print()
            sys.stdout.flush()
            num_errors = sum(
                1 for (checker, attempted, error) in tpls
                if attempted and error)
            num_attempted = sum(
                1 for (checker, attempted, error) in tpls if attempted)
            
            if not args.quiet:
                summary = " ".join(
                    "--" if not attempted else (
                        "ER" if error else "OK")
                    for (_, attempted, error) in tpls)
                print("[%3d / %3d] %s %s" % (
                    i + 1, len(rc), resource.name.ljust(55), summary))

                if args.verbose or num_attempted == 0 or num_errors > 0:
                    details_lines = []
                    for (check_num,
                            (_, attempted, error)) in enumerate(tpls):
                        if attempted:
                            message = error if error else "OK"
                        else:
                            message = "UNMATCHED"
                        if args.verbose or (attempted and error):
                            details_lines.extend(
                                textwrap.wrap(
                                    "[%d] %s" % (check_num, message),
                                    args.width,
                                    initial_indent=' ' * 4,
                                    subsequent_indent=' ' * 8))
                    details = "\n".join(details_lines)
                    if details:
                        print(details)
                        print()

            if num_attempted == 0 or num_errors > 0:
                problematic_resources.append(
                    (resource,
                        [(checker, error) for (checker, attempted, error)
                        in tpls
                        if attempted and error]))

        print()
        if problematic_resources:
            print("PROBLEMS (%d failed / %d total):" % (
                len(problematic_resources),
                len(rc)))
            for (resource, pairs) in problematic_resources:
                if not pairs:
                    print("UNMATCHED:")
                print(('{:-^%d}' % args.width).format(resource.name))
                print(resource)
                print()
                for (checker, error) in pairs:
                    print("\t%s" % checker)
                    print("\t---> %s" % error)
                    print()
        else:
            print("ALL OK")

    except resource_collection.NoCheckers:
        stderr("No checkers. Use the --checker argument to specify a checker.")
    