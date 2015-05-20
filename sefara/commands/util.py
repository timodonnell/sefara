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

from __future__ import absolute_import

from .. import load

def add_load_arguments(parser):
    parser.add_argument("collection")
    parser.add_argument("--filter", action="append", default=[])
    parser.add_argument("--decorate", action="append", default=[])
    return parser

def load_from_args(args):
    rc = load(args.collection)
    for value in args.filter:
        rc = rc.filter(value)
    for decorate in args.decorate:
        rc.decorate(decorate)
    return rc
