# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-29.
#=============================================================================
#   filtersuite.py --- Filter test suites
#=============================================================================
from compat import unittest


def flatten_suite(suite):
    def flatten(suite):
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                for t in flatten(test):
                    yield t
            else:
                yield test
    return unittest.TestSuite(flatten(suite))


def filter_suite(suite, failures):
    flattened = flatten_suite(suite)
    if not failures:
        return suite
    failed_tests = [test for test in flattened if str(test) in failures]
    return unittest.TestSuite(failed_tests) if failed_tests else suite


#.............................................................................
#   filtersuite.py
