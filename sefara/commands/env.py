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
Give current values of sefara environment variables.
'''

from __future__ import absolute_import, print_function

import sys
import os
import argparse

from .. import environment
from ..util import shell_quote

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

def run(argv=sys.argv[1:]):
    parser.parse_args(argv)

    variables = [
        environment.TRANSFORM_ENVIRONMENT_VARIABLE,
        environment.CHECKER_ENVIRONMENT_VARIABLE,
    ]

    for variable in variables:
        try:
            value = shell_quote(os.environ[variable])
        except KeyError:
            value = "<not set>"
        print("%s=%s" % (variable, value))
