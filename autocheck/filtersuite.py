# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-29.
#=============================================================================
#   filtersuite.py --- Testsuite with filter
#=============================================================================
from compat import unittest
from logger import Logger


class FilterSuite(unittest.TestSuite):
    
    def __init__(self, tests=()):
        super(FilterSuite, self).__init__(filter(self._accept_test, tests))
    
    def addTest(self, test):
        if self._accept_test(test):
            super(FilterSuite, self).addTest(test)
    
    def addTests(self, tests):
        super(FilterSuite, self).addTests(filter(self._accept_test, tests))
    
    def _accept_test(self, test):
        if self.failures is None:
            return True
        elif isinstance(test, unittest.TestSuite):
            return True
        else:
            return str(test) in self.failures


class FilterLoader(unittest.TestLoader, Logger):
    suiteClass = FilterSuite
    
    @classmethod
    def set_database(cls, database):
        if database is None:
            cls.failures = None
        else:
            last_run_id = database.get_last_run_id()
            last_successful_run_id = database.get_last_successful_run_id()
            last_successful_full_run_id = database.get_last_successful_full_run_id()
            if last_run_id is None:
                failures = None
            elif last_run_id == last_successful_full_run_id:
                failures = None
            elif last_run_id == last_successful_run_id:
                if last_successful_full_run_id is None:
                    failures = None
                else:
                    failures = set(database.collect_results_after(last_successful_full_run_id))
            else:
                failures = set(database.collect_results_after(last_successful_run_id))
        cls.suiteClass.failures = failures
        cls.suiteClass.full_suite = not failures
        cls.log.debug('%s/%s/%s:%s', last_run_id, last_successful_run_id, last_successful_full_run_id, failures)
        return not failures

#.............................................................................
#   filtersuite.py
