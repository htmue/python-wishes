# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   test_loader.py --- Feature test loader vows
#=============================================================================
from __future__ import unicode_literals

from functools import partial

import six
from should_dsl import should

from wishes import loader
from wishes.compat import unittest
from wishes.feature import Scenario, get_tags


class LoaderVows(unittest.TestCase):
    
    def test_returns_TestSuite_object(self):
        feature = loader.load_feature('Feature:')
        feature |should| be_instance_of(unittest.TestSuite)
    
    def test_returns_test_suite_consisting_of_TestCase_instances(self):
        feature = loader.load_feature('Feature:')
        test_case = six.next(iter(feature))
        test_case |should| be_instance_of(unittest.TestCase)
    
    def test_can_use_custom_TestCase_subclass(self):
        class MyTestCase(unittest.TestCase):
            pass
        feature = loader.load_feature('Feature:', test_case_class=MyTestCase)
        test_case = six.next(iter(feature))
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
        test_case = six.next(iter(feature))
        class_name = test_case.__class__.__name__
        class_name |should| be_equal_to('Feature_With_a_Title')
    
    def test_can_handle_special_characters_in_titles(self):
        feature = loader.load_feature('Feature: Für-wahr!')
        test_case = six.next(iter(feature))
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
        test_case = six.next(iter(feature))
        scenario_method = test_case._testMethodName
        scenario_method |should| be_equal_to('test_Scenario_Has_a_nice_Title')
    
    def test_stores_scenario_title_with_test_case(self):
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: Has a nice Title
        ''')
        test_case = six.next(iter(feature))
        test_case.scenario.title |should| be_equal_to('Has a nice Title')
    
    def test_can_use_custom_scenario_class(self):
        class MyScenario(Scenario):
            pass
        feature = loader.load_feature('''
        Feature: Load feature file
          Scenario: pending
        ''', scenario_class=MyScenario)
        test_case = six.next(iter(feature))
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
    
    def test_passes_on_hashes_to_scenario_add_step_method(self):
        calls = []
        class MyScenario(Scenario):
            def add_step(self, *args, **kwargs):
                calls.append((args, kwargs))
        feature = loader.load_feature('''
        Feature: with multiline scenarnio
          Scenario: with multiline step
            Given a step with hashes
              | first   | second    | third     |
              | first 1 | second 1  | third 1   |
              | first 2 | second 2  | third 2   |
        ''', scenario_class=MyScenario)
        len(calls) |should| be(1)
        args, kwargs = calls[0]
        args |should| be_equal_to(('Given', 'a step with hashes'))
        'hashes' |should| be_in(kwargs)
        list(kwargs['hashes']) |should| each_be_equal_to([
            dict(first='first 1', second='second 1', third='third 1'),
            dict(first='first 2', second='second 2', third='third 2'),
        ])
    
    def test_loads_feature_with_description(self):
        feature = loader.load_feature('''
        Feature: Load feature file
            With description
          Scenario: pending
        ''')
        test_case = six.next(iter(feature))
        test_case.description |should| be_equal_to('With description')

    def test_loads_feature_with_comment(self):
        feature = loader.load_feature('''
        # comment
        Feature: Load feature file
        ''')
        len(list(feature)) |should| be(1)


@unittest.skipIf(get_tags is None, 'get_tags() not available')
class TagLoaderVows(unittest.TestCase):
    
    def test_stores_tags_with_feature(self):
        feature = loader.load_feature('''
        @tag_1 @tag_2
        @tag_3
        Feature: features can have tags
          Scenario: with tags
        ''')
        test_case = six.next(iter(feature))
        tags = get_tags(test_case)
        sorted(tags) |should| each_be_equal_to(['tag_1', 'tag_2', 'tag_3'])
    
    def test_stores_tags_with_scenario(self):
        feature = loader.load_feature('''
        Feature: features can have tags
          @tag_1 @tag_2
          @tag_3
          Scenario: with tags
        ''')
        test_case = six.next(iter(feature))
        tags = get_tags(test_case)
        sorted(tags) |should| each_be_equal_to(['tag_1', 'tag_2', 'tag_3'])
    
    def test_clears_tags_between_scenarios(self):
        feature = loader.load_feature('''
        Feature: scenarios can have tags
          @tag
          Scenario: a) with a tag
          Scenario: b) without tags
        ''')
        test_case = list(feature)[1]
        tags = get_tags(test_case)
        tags |should| be_empty
    
    def test_mixes_tags_of_feature_and_scenario(self):
        feature = loader.load_feature('''
        @feature
        Feature: scenarios can have tags
          @scenario
          Scenario: with tag
          Scenario: without tags
        ''')
        test_cases = list(feature)
        tags = get_tags(test_cases[0])
        sorted(tags) |should| each_be_equal_to(['feature', 'scenario'])
        tags = get_tags(test_cases[1])
        sorted(tags) |should| each_be_equal_to(['feature'])
    
    def test_stores_background_tags_with_scenarios(self):
        feature = loader.load_feature('''
        Feature: background can have tags
          @background
          Background: with tag
          Scenario: without tags
          Scenario: also without tags
        ''')
        for test_case in feature:
            tags = get_tags(test_case)
            sorted(tags) |should| each_be_equal_to(['background'])
    
    def test_mixes_tags_of_background_and_scenario(self):
        feature = loader.load_feature('''
        Feature: background can have tags
          @background
          Background: with tag
          Scenario: a) without tags
          @scenario
          Scenario: b) with tag
        ''')
        test_cases = list(feature)
        tags = get_tags(test_cases[0])
        sorted(tags) |should| each_be_equal_to(['background'])
        tags = get_tags(test_cases[1])
        sorted(tags) |should| each_be_equal_to(['background', 'scenario'])
    
    def test_stores_outline_tags_with_scenarios(self):
        feature = loader.load_feature('''
        Feature: outlines can have tags
          @outline
          Scenario Outline: with tag
          Examples:
          | {a} | {var} |
          | one | line  |
          | and | next  |
        ''')
        for test_case in feature:
            tags = get_tags(test_case)
            sorted(tags) |should| each_be_equal_to(['outline'])
    
    def test_stores_examples_tags_with_scenarios(self):
        feature = loader.load_feature('''
        Feature: examples can have tags
          Scenario Outline: with tag
          @example
          Examples:
          | {a} | {var} |
          | one | line  |
          | and | next  |
        ''')
        for test_case in feature:
            tags = get_tags(test_case)
            sorted(tags) |should| each_be_equal_to(['example'])
    
    def test_mixes_tags_of_outline_and_examples_group(self):
        feature = loader.load_feature('''
        Feature: background can have tags
          @outline
          Scenario Outline: with tag
          Examples: 1
          | {a} | {var} |
          | one | line  |
          @example
          Examples: 2
          | {a} | {var} |
          | and | next  |
        ''')
        test_cases = list(feature)
        tags = get_tags(test_cases[0])
        sorted(tags) |should| each_be_equal_to(['outline'])
        tags = get_tags(test_cases[1])
        sorted(tags) |should| each_be_equal_to(['example', 'outline'])


#.............................................................................
#   test_loader.py
