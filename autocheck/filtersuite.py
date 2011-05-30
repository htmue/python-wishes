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
        return flattened
    failed_tests = [test for test in flattened if str(test) in failures]
    return unittest.TestSuite(failed_tests) if failed_tests else flattened


def filter_suite_from_database(suite, database):
    if database is None:
        return filter_suite(suite, set()), True
    last_run_id = database.get_last_run_id()
    last_successful_run_id = database.get_last_successful_run_id()
    last_successful_full_run_id = database.get_last_successful_full_run_id()
    if last_run_id is None:
        failures = set()
    elif last_run_id == last_successful_full_run_id:
        failures = set()
    elif last_run_id == last_successful_run_id:
        if last_successful_full_run_id is None:
            failures = set()
        else:
            failures = set(database.collect_results_after(last_successful_full_run_id))
    else:
        failures = set(database.collect_results_after(last_successful_run_id))
    return filter_suite(suite, failures), not failures


#.............................................................................
#   filtersuite.py
