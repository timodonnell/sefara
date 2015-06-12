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

"""
Functions used to define a resource collection.

These functions are intended to be called from resource collections defined
using Python, i.e. code in a file that you pass to ``load.load()``.
"""

from __future__ import absolute_import

from .resource import Resource

_EXPORTED_RESOURCES = []
def export(*args, **kwargs):
    """
    Create and export a Resource with the specified attributes.

    All arguments are passed to ``Resource``.
    """
    resource = Resource(*args, **kwargs)
    _EXPORTED_RESOURCES.append(resource)
    return resource

def export_resources(resources):
    """
    Export one or more Resource instances.

    Parameters
    ----------
    resources : list of Resource instances
        Resource instances to be exported.
    """
    _EXPORTED_RESOURCES.extend(resources)

_TRANSFORMS = []
def transform_exports(transformer):
    """
    

    """
    _TRANSFORMS.append(transformer)
    
