#!/usr/bin/env python

from __future__ import print_function

import sys, textwrap
print()
print("# The tool was invoked with these arguments:")
print("# " + "\n# ".join(textwrap.wrap(str(sys.argv[1:]))))
