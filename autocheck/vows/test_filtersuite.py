# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-30.
#=============================================================================
#   test_filtersuite.py --- FilterSuite vows
#=============================================================================
import os.path

import yaml
from should_dsl import should

from autocheck.compat import unittest
from autocheck.filtersuite import filter_suite, flatten_suite


class FilterSuiteTestCase(unittest.TestCase):
    __suites = yaml.load(open(os.path.splitext(__file__)[0] + '.yaml'))['suites']
    __cache = dict()
    
    class Test(unittest.TestCase):
        
        def runTest(self):
            pass
        
        @classmethod
        def add_test(cls, name):
            setattr(cls, 'test_' + name, cls.runTest)
    
    def get_suite(self, name):
        try:
            suite = self.__cache[name]
        except KeyError:
            suite = self.__cache[name] = self.add_suite(name, self.__suites[name])
        return suite
    
    def add_suite(self, name, defs):
        if not defs:
            return unittest.TestSuite()
        elif isinstance(defs, list):
            return self.add_tests(name, defs)
        elif isinstance(defs, dict):
            return self.add_suites(name, defs)
        else:
            raise RuntimeError('invalid suite definition: %s' % defs)
    
    def add_suites(self, name, defs):
        return unittest.TestSuite(
            self.add_suite('_'.join((name, key)), value)
            for key, value in sorted(defs.items())
        )
    
    def add_tests(self, name, defs):
        class Test(self.Test): pass
        Test.__name__ = 'Test_' + name
        for test_name in defs:
            Test.add_test(test_name)
        return unittest.defaultTestLoader.loadTestsFromTestCase(Test)


class FilterSuiteTestCaseVows(FilterSuiteTestCase):
    
    def test_returns_TestSuite_instance(self):
        suite = self.get_suite('empty')
        
        suite |should| be_instance_of(unittest.TestSuite)
    
    def test_handles_empty_suite_properly(self):
        suite = self.get_suite('empty')
        
        map(str, suite) |should| each_be_equal_to([])
    
    def test_handles_flat_suite_properly(self):
        suite = self.get_suite('flat')
        
        map(str, suite) |should| each_be_equal_to([
    	    'test_one (autocheck.vows.test_filtersuite.Test_flat)',
    	    'test_three (autocheck.vows.test_filtersuite.Test_flat)',
    	    'test_two (autocheck.vows.test_filtersuite.Test_flat)',
        ])
    
    def test_handles_nested_suite_properly(self):
        suite = self.get_suite('nested')
        
        map(str, suite) |should| each_be_equal_to([
            '<unittest.suite.TestSuite tests=['
                '<autocheck.vows.test_filtersuite.Test_nested_first testMethod=test_one>, '
                '<autocheck.vows.test_filtersuite.Test_nested_first testMethod=test_two>]>',
            '<unittest.suite.TestSuite tests=['
                '<autocheck.vows.test_filtersuite.Test_nested_second testMethod=test_four>, '
                '<autocheck.vows.test_filtersuite.Test_nested_second testMethod=test_three>]>',
        ])
    
    def test_handles_mixed_suite_properly(self):
        suite = self.get_suite('mixed')
        
        map(str, suite) |should| each_be_equal_to([
            '<unittest.suite.TestSuite tests=['
                '<autocheck.vows.test_filtersuite.Test_mixed_flat testMethod=test_one>, '
                '<autocheck.vows.test_filtersuite.Test_mixed_flat testMethod=test_two>]>',
            '<unittest.suite.TestSuite tests=['
                '<unittest.suite.TestSuite tests=['
                    '<autocheck.vows.test_filtersuite.Test_mixed_nested_first testMethod=test_four>, '
                    '<autocheck.vows.test_filtersuite.Test_mixed_nested_first testMethod=test_three>]>, '
                '<unittest.suite.TestSuite tests=['
                    '<autocheck.vows.test_filtersuite.Test_mixed_nested_second testMethod=test_five>, '
                    '<autocheck.vows.test_filtersuite.Test_mixed_nested_second testMethod=test_six>]>, '
                    '<unittest.suite.TestSuite tests=['
                        '<unittest.suite.TestSuite tests=['
                            '<autocheck.vows.test_filtersuite.Test_mixed_nested_third_deep testMethod=test_eight>, '
                            '<autocheck.vows.test_filtersuite.Test_mixed_nested_third_deep testMethod=test_seven>]>]>]>',
        ])


class FlattenSuiteVows(FilterSuiteTestCase):
    
    def test_returns_TestSuite_instance(self):
        suite = self.get_suite('empty')
        
        flattened = flatten_suite(suite)
        
        flattened |should| be_instance_of(unittest.TestSuite)
    
    def test_handles_empty_suite_properly(self):
        suite = self.get_suite('empty')
        
        flattened = flatten_suite(suite)
        
        next = iter(flattened).next
        next |should| throw(StopIteration)
    
    def test_handles_flat_suite_properly(self):
        suite = self.get_suite('flat')
        
        flattened = flatten_suite(suite)
        
        map(str, flattened) |should| each_be_equal_to([
    	    'test_one (autocheck.vows.test_filtersuite.Test_flat)',
    	    'test_three (autocheck.vows.test_filtersuite.Test_flat)',
    	    'test_two (autocheck.vows.test_filtersuite.Test_flat)',
        ])
    
    def test_handles_nested_suite_properly(self):
        suite = self.get_suite('nested')
        
        flattened = flatten_suite(suite)
        
        map(str, flattened) |should| each_be_equal_to([
            'test_one (autocheck.vows.test_filtersuite.Test_nested_first)',
            'test_two (autocheck.vows.test_filtersuite.Test_nested_first)',
            'test_four (autocheck.vows.test_filtersuite.Test_nested_second)',
            'test_three (autocheck.vows.test_filtersuite.Test_nested_second)',
        ])
    
    def test_handles_mixed_suite_properly(self):
        suite = self.get_suite('mixed')
        
        flattened = flatten_suite(suite)
        
        map(str, flattened) |should| each_be_equal_to([
            'test_one (autocheck.vows.test_filtersuite.Test_mixed_flat)',
            'test_two (autocheck.vows.test_filtersuite.Test_mixed_flat)',
            'test_four (autocheck.vows.test_filtersuite.Test_mixed_nested_first)',
            'test_three (autocheck.vows.test_filtersuite.Test_mixed_nested_first)',
            'test_five (autocheck.vows.test_filtersuite.Test_mixed_nested_second)',
            'test_six (autocheck.vows.test_filtersuite.Test_mixed_nested_second)',
            'test_eight (autocheck.vows.test_filtersuite.Test_mixed_nested_third_deep)',
            'test_seven (autocheck.vows.test_filtersuite.Test_mixed_nested_third_deep)',
        ])


class FilterSuiteVows(FilterSuiteTestCase):
    
    def test_returns_TestSuite_instance(self):
        suite = self.get_suite('empty')
        
        filtered = filter_suite(suite, set())
        
        filtered |should| be_instance_of(unittest.TestSuite)
    
    def test_returns_all_tests_when_failures_empty(self):
        suite = self.get_suite('flat')
        
        filtered = filter_suite(suite, set())
        
        map(str, filtered) |should| each_be_equal_to(map(str, flatten_suite(suite)))
    
    def test_returns_only_tests_from_failures(self):
        suite = self.get_suite('flat')
        failures = ['test_two (autocheck.vows.test_filtersuite.Test_flat)']
        
        filtered = filter_suite(suite, set(failures))
        
        map(str, filtered) |should| each_be_equal_to(failures)
    
    def test_returns_all_tests_when_filtered_empty(self):
        suite = self.get_suite('flat')
        
        filtered = filter_suite(suite, set(['unknown']))
        
        map(str, filtered) |should| each_be_equal_to(map(str, flatten_suite(suite)))


#.............................................................................
#   test_filtersuite.py
