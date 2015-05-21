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
Check a sefara resource.
'''

from __future__ import absolute_import, print_function

import argparse
import sys

from . import util
from .. import resource_collection

parser = argparse.ArgumentParser(usage=__doc__)
util.add_load_arguments(parser)
parser.add_argument("--checker", action="append", default=[])
parser.add_argument("--no-environment-checkers",
        dest="environment_checkers",
        action="store_false",
        default=True)
parser.add_argument("--format", choices=('human', 'json'), default="human")
parser.add_argument("--out")
parser.add_argument("--verbose", action="store_true", default=False)
parser.add_argument("--quiet", action="store_true", default=False)
parser.add_argument("--indent", type=int, default=4)

def run():
    args = parser.parse_args()
    rc = util.load_from_args(args)

    try:
        results = rc.check(
            args.checker,
            include_environment_checkers=args.environment_checkers)
    except resource_collection.NoCheckers:
        results = None

    fd = open(args.out, "w") if args.out else sys.stdout

    def fdprint(s=""):
        print(s, file=fd)

    try:
        if args.format == "human":
            if results is None:
                fdprint("No checkers. Use the --checker argument to specify a "
                    "checker.")
                return

            problematic_datasets = []
            for (i, (resource, tpls)) in enumerate(results):
                if i == 0:
                    fdprint("Checkers:")
                    for (checker_num, (checker, _, _)) in enumerate(tpls):
                        print("\t[%d]\t%s" % (checker_num, checker))
                fdprint()
                num_errors = sum(
                    1 for (_, attempted, error) in tpls
                    if attempted and error)
                num_attempted = sum(
                    1 for (_, attempted, _) in tpls if attempted)
                
                if not args.quiet:
                    if num_errors == 0 and num_attempted > 0:
                        summary = "OK (%d checked)" % num_attempted
                    elif num_attempted == 0:
                        summary = "UNMATCHED"
                    else:
                        summary = "ERROR (%d error / %d checked)" % (
                            num_errors, num_attempted)
                    fdprint("[%3d / %3d] %s %s" % (
                        i + 1, len(rc), resource.name.rfill(30), summary))

                if args.verbose or num_attempted == 0 or num_errors > 0:
                    details_lines = []
                    for (check_num, (_, attempted, error)) in enumerate(tpls):
                        if attempted:
                            message = error if error else "OK"
                        else:
                            message = "UNMATCHED"
                        if args.verbose or (attempted and error):
                            details_lines.append(
                                "\t[%d]\t%s" % (checker_num, message))
                    details = "\n".join(details_lines)
                    fdprint(details)

                if num_attempted == 0 or num_errors > 0:
                    problematic_datasets.append(resource)

            fdprint()
            if problematic_datasets:
                fdprint("PROBLEMATIC RESOURCES: %s"
                    % " ".join(problematic_datasets))
            else:
                fdprint("ALL RESOURCES OK")

        elif args.format == "json":
            raise NotImplementedError()
        else:
            raise ValueError("Unknown format: %s" % format)
    finally:
        fd.close()
