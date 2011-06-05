# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-18.
#=============================================================================
#   compat.py --- Compatibility for Python 2.6
#=============================================================================

import sys
if sys.version_info[:2] < (2, 7):
    try:
        from django.utils import unittest
    except ImportError:
        import unittest2 as unittest
else:
    import unittest

try:
    from itertools import combinations_with_replacement
except ImportError:
    def combinations_with_replacement(iterable, r):
        # combinations_with_replacement('ABC', 2) --> AA AB AC BB BC CC
        pool = tuple(iterable)
        n = len(pool)
        if not n and r:
            return
        indices = [0] * r
        yield tuple(pool[i] for i in indices)
        while True:
            for i in reversed(range(r)):
                if indices[i] != n - 1:
                    break
            else:
                return
            indices[i:] = [indices[i] + 1] * (r - i)
            yield tuple(pool[i] for i in indices)

#.............................................................................
#   compat.py

# combinations_with_replacement taken from Python-2.7.1 itertools documentation
# Copyright © 2001-2010 Python Software Foundation; All Rights Reserved
# http://docs.python.org/license.html
