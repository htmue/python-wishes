# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_feature.py --- Wishes feature vows
#=============================================================================
from __future__ import unicode_literals

import mock
import six
from should_dsl import should

from wishes.compat import unittest
from wishes.feature import FeatureTest, step, StepDefinition, World
from wishes.loader import load_feature


class FeatureVows(unittest.TestCase):
    
    def setUp(self):
        StepDefinition.clear()
    
    def test_can_run_feature(self):
        @step('there is a step')
        def there_is_a_step(step):
            my_world.there_is_a_step = True
        @step('another step')
        def another_step(step):
            my_world.another_step = True
        @step('steps afterwards')
        def steps_afterwards(step):
            my_world.steps_afterwards = True
        feature = load_feature('''
        Feature: run a feature
          Scenario: some steps
            Given there is a step
            And another step
            When I add something undefined
            Then steps afterwards are not run
        ''')
        my_world = World()
        my_world.there_is_a_step = False
        my_world.another_step = False
        my_world.steps_afterwards = False
        result = unittest.TestResult()
        
        feature.run(result)
        
        len(result.skipped) |should| be(1)
        result.skipped[0][1] |should| start_with('pending 1 step(s):')
        run = my_world.there_is_a_step, my_world.another_step, my_world.steps_afterwards
        run |should| be_equal_to((True, True, False))
    
    def test_can_run_feature_with_background(self):
        @step('background step')
        def background_step(step):
            my_world.background_step += 1
        @step('scenario step ([0-9]+)')
        def scenario_step_number(step, number):
            my_world.steps_run.append(int(number))
        feature = load_feature('''
        Feature: with background
          Background: present
            Given a background step
          Scenario: with background 1
            And a scenario step 1
          Scenario: with background 2
            And a scenario step 2
        ''')
        my_world = World()
        my_world.background_step = 0
        my_world.steps_run = []
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        my_world.background_step |should| be(2)
        my_world.steps_run |should| be_equal_to([1, 2])
    
    
    def test_can_run_feature_with_multiple_backgrounds(self):
        @step('background step ([0-9]+)')
        def background_step_number(step, number):
            my_world.background_number = number
        @step('scenario step ([0-9]+)')
        def scenario_step_number(step, number):
            my_world.background_number |should| be_equal_to(number)
            my_world.steps_run.append(int(number))
        feature = load_feature('''
        Feature: with background
          Background: 1 present
            Given a background step 1
          Scenario: with background 1
            And a scenario step 1
          Background: 2 present
            Given a background step 2
          Scenario: with background 2
            And a scenario step 2
        ''')
        my_world = World()
        my_world.steps_run = []
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        my_world.steps_run |should| be_equal_to([1, 2])
    
    def test_can_run_feature_with_multiline_step(self):
        @step('multiline step')
        def multiline_step(step):
            my_world.multiline = step.multiline
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario: with multiline step
            Given a multiline step
              """
              multiline content
              """
        ''')
        my_world = World()
        my_world.multiline = None
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)
        my_world.multiline |should| be_equal_to('multiline content\n')
    
    def test_can_run_feature_with_hashes_step(self):
        @step('step with hashes')
        def step_with_hashes(step):
            my_world.hashes = step.hashes
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario: with multiline step
            Given a step with hashes
              | first   | second    | third     |
              | first 1 | second 1  | third 1   |
              | first 2 | second 2  | third 2   |
        ''')
        my_world = World()
        my_world.hashes = None
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)
        list(my_world.hashes) |should| each_be_equal_to([
            dict(first='first 1', second='second 1', third='third 1'),
            dict(first='first 2', second='second 2', third='third 2'),
        ])
    
    def test_can_run_feature_with_hashes_in_background_step(self):
        @step('step with hashes')
        def step_with_hashes(step):
            my_world.hashes = step.hashes
        @step('here it is')
        def here_it_is(step):
            pass
        feature = load_feature('''
        Feature: with multiline scenarnio
          Background: with multiline step
            Given a step with hashes
              | first   | second    | third     |
              | first 1 | second 1  | third 1   |
              | first 2 | second 2  | third 2   |
          Scenario: with defined step
            And here it is
        ''')
        my_world = World()
        my_world.hashes = None
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)
        my_world.hashes |should| each_be_equal_to([
            dict(first='first 1', second='second 1', third='third 1'),
            dict(first='first 2', second='second 2', third='third 2'),
        ])
    
    def test_can_run_feature_with_scenario_outline_and_examples(self):
        @step('a (.*) with (.*)')
        def a_key_with_value(step, key, value):
            my_world.run.append((key, value))
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario Outline: follows
            Given a <key> with <value>
          Examples:
            | key   | value     |
            | key 1 | value 1   |
            | key 2 | value 2   |
        ''')
        my_world = World()
        my_world.run = []
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        my_world.run |should| each_be_equal_to([
            ('key 1', 'value 1'),
            ('key 2', 'value 2'),
        ])
    
    def test_can_run_feature_with_scenario_outline_with_multiline(self):
        @step('a multiline')
        def a_multiline(step):
            my_world.run.append(step.multiline)
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario Outline: follows
            Given a multiline
              """
              with <placeholder>
              """
          Examples:
            | <placeholder> |
            | first         |
            | second        |
        ''')
        my_world = World()
        my_world.run = []
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        my_world.run |should| each_be_equal_to([
            'with first\n',
            'with second\n',
        ])
    
    def test_can_run_feature_with_scenario_outline_with_hashes(self):
        @step('a hash')
        def a_hash(step):
            my_world.run.append(list(step.hashes))
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario Outline: follows
            Given a hash
              | <key>   | value         |
              | the     | <placeholder> |
          Examples:
            | <key> | <placeholder> |
            | key   | first         |
            | but   | second        |
        ''')
        my_world = World()
        my_world.run = []
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        my_world.run |should| each_be_equal_to([
            [dict(key='the', value='first')],
            [dict(but='the', value='second')],
        ])
    
    def test_can_run_feature_with_scenario_outline_with_background(self):
        @step('a (.*)')
        def a_something(step, value):
            my_world.run.append(value)
        feature = load_feature('''
        Feature: with multiline scenarnio
          Background: with placeholder
            Given a <placeholder>
          Scenario Outline: follows
            And a step
          Examples:
            | <placeholder> |
            | first         |
            | second        |
        ''')
        my_world = World()
        my_world.run = []
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        my_world.run |should| each_be_equal_to([
            'first', 'step', 'second', 'step',
        ])
    
    def run_feature_with_result_step_handlers(self, feature, *handlers):
        result = unittest.TestResult()
        for handler in ['startStep', 'stopStep'] + list(handlers):
            setattr(result, handler, mock.Mock(handler))
        
        feature.run(result)
        
        result.testsRun |should| be(1)
        result.startStep.call_count |should| be(1)
        result.stopStep.call_count |should| be(1)
        return result
    
    def test_reports_steps_to_result_object(self):
        @step('some step')
        def some_step(step):
            pass
        feature = load_feature('''
        Feature: report steps
          Scenario: with a step
            Given there is some step
        ''')
        result = self.run_feature_with_result_step_handlers(feature)
        result.wasSuccessful() |should| be(True)
    
    def test_reports_step_success_to_result_object(self):
        @step('some step')
        def some_step(step):
            pass
        feature = load_feature('''
        Feature: report steps
          Scenario: with a step
            Given there is some step
        ''')
        result = self.run_feature_with_result_step_handlers(feature, 'addStepSuccess')
        result.wasSuccessful() |should| be(True)
        result.addStepSuccess.call_count |should| be(1)
    
    def test_reports_step_failure_to_result_object(self):
        @step('some failing step')
        def some_step(step):
            1 |should| be(2)
        feature = load_feature('''
        Feature: report steps
          Scenario: with a step
            Given there is some failing step
        ''')
        result = self.run_feature_with_result_step_handlers(feature, 'addStepFailure')
        result.wasSuccessful() |should| be(False)
        result.addStepFailure.call_count |should| be(1)
    
    def test_reports_step_error_to_result_object(self):
        @step('some error step')
        def some_step(step):
            raise Exception('hey')
        feature = load_feature('''
        Feature: report steps
          Scenario: with a step
            Given there is some error step
        ''')
        result = self.run_feature_with_result_step_handlers(feature, 'addStepError')
        result.wasSuccessful() |should| be(False)
        result.addStepError.call_count |should| be(1)
    
    def test_reports_undefined_step_to_result_object(self):
        feature = load_feature('''
        Feature: report steps
          Scenario: with a step
            Given there is some undefined step
        ''')
        result = self.run_feature_with_result_step_handlers(feature, 'addStepUndefined')
        len(result.skipped) |should| be(1)
        result.wasSuccessful() |should| be(True)
        result.addStepUndefined.call_count |should| be(1)
    
    def test_clears_world_between_scenarios(self):
        @step('set a world var')
        def set_world(step):
            step.world.var = 'set'
        @step('check that world var')
        def check_var(step):
            getattr(step.world, 'var', None) |should| be(None)
        feature = load_feature('''
        Feature: clears world between scenarios
          Scenario: first
            When I set a world var
          Scenario: second
            Then I check that world var
        ''')
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
    
    def test_makes_itself_accessible_through_world(self):
        @step('feature attribute is set to "(.*)"')
        def feature_attribute(step, name):
            step.world.feature |should| be_instance_of(FeatureTest)
            step.world.feature.__class__.__name__ |should| be_equal_to(name)
        feature = load_feature('''
        Feature: accessible through world
          Scenario: test
            Then the feature attribute is set to "Feature_accessible_through_world"
        ''')
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)
    
    def test_can_provide_custom_world_class(self):
        class MyWorld(World):
            pass
        class MyFeature(unittest.TestCase):
            World = MyWorld
        @step('world is an instance of the MyWorld class')
        def world_is_instance_of(step):
            step.world |should| be_instance_of(MyWorld)
        feature = load_feature('''
        Feature: custom world class
          Scenario: test
            Then world is an instance of the MyWorld class
        ''', test_case_class=MyFeature)
        result = unittest.TestResult()
        
        feature.run(result)
        
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)

    def test_has_shortDescription_when_empty(self):
        feature = load_feature('Feature: empty')
        test = six.next(iter(feature))
        
        test.shortDescription() |should| be_equal_to('Feature: empty')

#.............................................................................
#   test_feature.py
