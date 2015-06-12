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
import textwrap

from . import util
from .. import resource_collection
from .util import print_stderr as stderr

parser = argparse.ArgumentParser(description=__doc__)
util.add_load_arguments(parser)
parser.add_argument("--checker", action="append", default=[])
parser.add_argument("--no-environment-checkers",
        dest="environment_checkers",
        action="store_false",
        default=True)
parser.add_argument("--format", choices=('human', 'json'), default="human")
parser.add_argument("--out")
parser.add_argument("-v", "--verbose", action="store_true", default=False)
parser.add_argument("-q", "--quiet", action="store_true", default=False)
parser.add_argument("--width", type=int, default=100)

def run(argv=sys.argv[1:]):
    args = parser.parse_args(argv)
    rc = util.load_from_args(args)

    results = rc.check(
        args.checker,
        include_environment_checkers=args.environment_checkers)

    fd = open(args.out, "w") if args.out else sys.stdout

    def fdprint(s=""):
        print(s, file=fd)

    try:
        if args.format == "human":
            problematic_resources = []
            for (i, (resource, tpls)) in enumerate(results):
                if i == 0:
                    fdprint("Checkers:")
                    for (checker_num, (checker, _, _)) in enumerate(tpls):
                        print("\t[%d]\t%s" % (checker_num, checker))
                    fdprint()
                fd.flush()
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
                    fdprint("[%3d / %3d] %s %s" % (
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
                            fdprint(details)
                            fdprint()

                if num_attempted == 0 or num_errors > 0:
                    problematic_resources.append(
                        (resource,
                            [(checker, error) for (checker, attempted, error)
                            in tpls
                            if attempted and error]))

            fdprint()
            if problematic_resources:
                fdprint("PROBLEMS (%d failed / %d total):" % (
                    len(problematic_resources),
                    len(rc)))
                for (resource, pairs) in problematic_resources:
                    if not pairs:
                        fdprint("UNMATCHED:")
                    fdprint(('{:-^%d}' % args.width).format(resource.name))
                    fdprint(resource)
                    fdprint()
                    for (checker, error) in pairs:
                        fdprint("\t%s" % checker)
                        fdprint("\t---> %s" % error)
                        fdprint()
            else:
                fdprint("ALL OK")

        elif args.format == "json":
            raise NotImplementedError()
        else:
            raise ValueError("Unknown format: %s" % format)
    except resource_collection.NoCheckers:
        stderr("No checkers. Use the --checker argument to specify a checker.")
    finally:
        fd.close()
