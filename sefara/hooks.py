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
Hooks are a mechanism for running site-specific transforms or validation
routines on Sefara resources.
"""

from __future__ import absolute_import

import os
from . import environment
from .util import exec_in_directory

class NoCheckers(Exception):
    pass

def transform_from_environment(collection):
    """
    Run the environment-variable-defined transforms on the resources in
    the collection. The transforms will mutate the resources in this
    collection; a new ResourceCollection is NOT returned.

    See the `environment` module for the definition of the environment
    variable used here.
    """
    transforms = os.environ.get(
        environment.TRANSFORM_ENVIRONMENT_VARIABLE, "").split(":")

    for t in transforms:
        t = t.strip()
        if t:
            transform(collection, t)

def transform(collection, path_or_callable, name='transform', *args, **kwargs):
    """
    Run a function on the resources in the collection. The function is
    expected to mutate the resources in the collection; a new collection
    is NOT returned.

    Parameters
    ----------
    path_or_callable : string or callable
        If string, then this is interpreted as a path to a Python file. The
        file will be exec'd and is expected to define a module attribute
        given by the `name` argument. This attribute will be used as the
        callable. It should take a ResourceCollection instance as an
        argument.

        Otherwise, this parameter should be a callable that takes a
        ResourceCollection instance. It will be invoked on this
        ResourceCollection.

    name : string [optional, default 'transform']
        If `path_or_callable` is a string giving a path to a Python file
        to execute, this parameter gives the attribute in that module to
        use as the callable. Defaults to "transform", i.e. the Python file
        specified by `path_or_callable` is expected to define a function
        called "transform".

    *args, **kwargs
        Additional args and kwargs are passed to the transform function.
    """
    run_hook(collection, path_or_callable, name, *args, **kwargs)

def check(collection, checkers=None, include_environment_checkers=True):
    '''
    Run "checkers", either specified as an argument or using environment
    variables, on the resource collection.

    Checkers are used to validate that the resources in a collection
    meet user-defined criteria, for example, that the paths they point
    to exist.

    Parameters
    ----------
    checkers : list of either callables, strings, or tuples [optional]
        
        If tuples, the elements are ``(path, name, args, kwargs)``.

        Like transforms, checkers are called with this ResourceCollection
        instance as an argument. Unlike transforms, checkers should NOT
        mutate the resources. They are expected to return a list or
        generator of three element tuples, ``(resource, attempted, problem)``
        where ``resource`` is a Resource in this collection, ``attempted``
        is True if validation was attempted on this resource, and
        ``problem`` is a string error message if validation was unsuccesful
        (None otherwise).

        By returning ``attempted=False`` in the tuple above, checkers
        indicate that a resource did not conform to the schema the checker
        knows how to validate. For example, a checker might be verifying
        that files pointed to by resources exist, but some resource may not
        specify any file. In this case, the checker should set
        ``attempted=False``. Another checker in use may know how to
        validate that resource. The ``sefara-check`` tool reports any
        resources that were not attempted by any checker as an error.

        Checkers should generate a tuple for *every* resource in the
        collection *in the order they appear in the collection*.

    include_environment_checkers : boolean [optional, default: True]
        If True, then checkers configured in environment variables are run,
        in addition to any checkers specified in the first argument.

        See the `environment` module for the definition of the environment
        variable used here.

    Returns
    ----------
    Generator giving (resource, tuples) pairs, where resource is a Resource
    in this collection, and tuples is a list of
    ``(checker, attempted, error)`` giving whether each checker
    attempted validation of that resource, and, if so, the result.
    ``error`` is None if validation was successful, otherwise a string
    giving the error.
    '''
    if checkers is None:
        checkers = []

    if include_environment_checkers:
        checkers.extend(
            e.strip()
            for e in os.environ.get(
                environment.CHECKER_ENVIRONMENT_VARIABLE, "").split(":")
            if e.strip())

    generators = []
    for checker in checkers:
        if isinstance(checker, tuple):
            (path, name, args, kwargs) = checker
            generator = run_hook(collection, path, name, *args, **kwargs)
        else:
            generator = run_hook(collection, checker, name="check")
        generators.append(generator)

    if not generators:
        raise NoCheckers()

    for row in zip(collection, *generators):
        (expected_resource, results) = (row[0], row[1:])
        tuples = []  # (checker, attempted, error)
        for (i, (resource, attempted, error)) in enumerate(results):
            if resource != expected_resource:
                raise ValueError(
                    "Checker %d (%s): skipping / reordering: %s != %s"
                    % (i, checkers[i], resource, expected_resource))
            tuples.append((str(checkers[i]), attempted, error))
        yield (expected_resource, tuples) 

def run_hook(collection, path_or_callable, name, *args, **kwargs):
    """
    Invoke a Python callable (either passed directly or defined in the
    specified Python file) on the ResourceCollection and return the
    result.

    Parameters
    ----------
    path_or_callable : string or callable
        If string, then this is interpreted as a path to a Python file. The
        file will be exec'd and is expected to define a module attribute
        given by the `name` argument. This attribute will be used as the
        callable. It should take a ResourceCollection instance as an
        argument.

        Otherwise, this parameter should be a callable that takes a
        ResourceCollection instance. It will be invoked on this
        ResourceCollection.

    name : string [optional, default 'transform']
        If `path_or_callable` is a string giving a path to a Python file
        to execute, this parameter gives the attribute in that module to
        use as the callable.

    *args, **kwargs
        Additional args and kwargs are passed to the callable after the
        ResourceCollection.
    """
    if hasattr(path_or_callable, '__call__'):
        function = path_or_callable
    else:
        filename = path_or_callable
        defines = exec_in_directory(filename)
        try:
            function = defines[name]
        except KeyError:
            raise AttributeError(
                "Hook '%s' defines no such field '%s'"
                % (filename, name))
    return function(collection, *args, **kwargs)
