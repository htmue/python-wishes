# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   test_loader.py --- Feature test loader vows
#=============================================================================
import unittest
from functools import partial

from should_dsl import should

from wishes import loader
from wishes.feature import Scenario


class LoaderTest(unittest.TestCase):
    
    def test_returns_TestSuite_object(self):
        feature = loader.load_feature('Feature:')
        feature |should| be_instance_of(unittest.TestSuite)
    
    def test_returns_test_suite_consisting_of_TestCase_instances(self):
        feature = loader.load_feature('Feature:')
        test_case = iter(feature).next()
        test_case |should| be_instance_of(unittest.TestCase)
    
    def test_can_use_custom_TestCase_subclass(self):
        class MyTestCase(unittest.TestCase):
            pass
        feature = loader.load_feature('Feature:', test_case_class=MyTestCase)
        test_case = iter(feature).next()
        test_case |should| be_instance_of(MyTestCase)
    
    def test_rejects_custom_test_case_class_that_is_not_TestCase_subclass(self):
        class MyTestCase(object):
            pass
        load_feature = partial(loader.load_feature, 'Feature:', test_case_class=MyTestCase)
        load_feature |should| throw(ValueError)
    
    def test_marks_Feature_as_skipped_when_no_scenarios_are_defined(self):
        feature = loader.load_feature('Feature:')
        result = unittest.TestResult()
        feature.run(result)
        len(result.skipped) |should| be(1)
        result.skipped[0][1] |should| be_equal_to('no scenarios defined')
    
    def test_generates_class_name_from_feature_title(self):
        feature = loader.load_feature('Feature: With a Title')
        test_case = iter(feature).next()
        class_name = test_case.__class__.__name__
        class_name |should| be_equal_to('Feature_With_a_Title')
    
    def test_can_handle_special_characters_in_titles(self):
        feature = loader.load_feature('Feature: Für-wahr!')
        test_case = iter(feature).next()
        class_name = test_case.__class__.__name__
        class_name |should| be_equal_to('Feature_Fur_wahr')
    
    def test_creates_one_test_method_per_scenario(self):
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: pending
          Scenario: second one
        ''')
        feature.countTestCases() |should| be(2)
    
    def test_marks_scenarios_without_steps_as_skipped(self):
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: pending
        ''')
        result = unittest.TestResult()
        feature.run(result)
        len(result.skipped) |should| be(1)
        result.skipped[0][1] |should| be_equal_to('no steps defined')
    
    def test_generates_test_names_from_scenario_title(self):
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: Has a nice Title
        ''')
        test_case = iter(feature).next()
        scenario_method = test_case._testMethodName
        scenario_method |should| be_equal_to('test_Scenario_Has_a_nice_Title')
    
    def test_stores_scenario_title_with_test_case(self):
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: Has a nice Title
        ''')
        test_case = iter(feature).next()
        test_case.scenario.title |should| be_equal_to('Has a nice Title')

    def test_can_use_custom_scenario_class(self):
        class MyScenario(Scenario):
            pass
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: pending
        ''', scenario_class=MyScenario)
        test_case = iter(feature).next()
        test_case.scenario |should| be_instance_of(MyScenario)

    def test_rejects_custom_scenario_class_that_is_not_Scenario_subclass(self):
        class MyScenario(object):
            pass
        load_feature = partial(loader.load_feature, 'Feature:', scenario_class=MyScenario)
        load_feature |should| throw(ValueError)
    
    def test_passes_on_steps_to_scenario_add_step_method(self):
        calls = []
        class MyScenario(Scenario):
            def add_step(self, *args, **kwargs):
                calls.append((args, kwargs))
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: with step
            When step is defined
        ''', scenario_class=MyScenario)
        len(calls) |should| be(1)

    def test_passes_on_multiline_content_to_scenario_add_step_method(self):
        calls = []
        class MyScenario(Scenario):
            def add_step(self, *args, **kwargs):
                calls.append((args, kwargs))
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: with step
            Given a multiline step
              """
              multiline content
              """
        ''', scenario_class=MyScenario)
        len(calls) |should| be(1)
        calls[0] |should| each_be_equal_to((
            ('Given', 'a multiline step'), dict(multilines=['multiline content\n'])
        ))

#.............................................................................
#   test_loader.py
