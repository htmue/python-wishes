# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_feature.py --- Wishes feature vows
#=============================================================================
import unittest

from should_dsl import should

from wishes.feature import world, StepDefinition, step
from wishes.loader import load_feature


class FeatureTest(unittest.TestCase):
    
    def setUp(self):
        StepDefinition.clear()
    
    def test_can_run_feature(self):
        @step('there is a step')
        def there_is_a_step(step):
            world.there_is_a_step = True
        @step('another step')
        def another_step(step):
            world.another_step = True
        @step('steps afterwards')
        def steps_afterwards(step):
            world.steps_afterwards = True
        feature = load_feature('''
        Feature: run a feature
          Scenario: some steps
            Given there is a step
            And another step
            When I add something undefined
            Then steps afterwards are not run
        ''')
        world.there_is_a_step = False
        world.another_step = False
        world.steps_afterwards = False
        result = unittest.TestResult()
        feature.run(result)
        len(result.skipped) |should| be(1)
        result.skipped[0][1] |should| be_equal_to('pending 1 step(s)')
        run = world.there_is_a_step, world.another_step, world.steps_afterwards
        run |should| be_equal_to((True, True, False))
    
    def test_can_run_feature_with_background(self):
        @step('background step')
        def background_step(step):
            world.background_step += 1
        @step('scenario step ([0-9]+)')
        def scenario_step_number(step, number):
            world.steps_run.append(int(number))
        feature = load_feature('''
        Feature: with background
          Background: present
            Given a background step
          Scenario: with background 1
            And a scenario step 1
          Scenario: with background 2
            And a scenario step 2
        ''')
        world.background_step = 0
        world.steps_run = []
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        world.background_step |should| be(2)
        world.steps_run |should| be_equal_to([1, 2])
    
    
    def test_can_run_feature_with_multiple_backgrounds(self):
        @step('background step ([0-9]+)')
        def background_step_number(step, number):
            world.background_number = number
        @step('scenario step ([0-9]+)')
        def scenario_step_number(step, number):
            world.background_number |should| be_equal_to(number)
            world.steps_run.append(int(number))
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
        world.steps_run = []
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        world.steps_run |should| be_equal_to([1, 2])
    
    def test_can_run_feature_with_multiline_step(self):
        @step('multiline step')
        def multiline_step(step):
            world.multiline = step.multiline
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario: with multiline step
            Given a multiline step
              """
              multiline content
              """
        ''')
        world.multiline = None
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)
        world.multiline |should| be_equal_to('multiline content\n')
    
    def test_can_run_feature_with_hashes_step(self):
        @step('step with hashes')
        def step_with_hashes(step):
            world.hashes = step.hashes
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario: with multiline step
            Given a step with hashes
              | first   | second    | third     |
              | first 1 | second 1  | third 1   |
              | first 2 | second 2  | third 2   |
        ''')
        world.hashes = None
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)
        list(world.hashes) |should| each_be_equal_to([
            dict(first='first 1', second='second 1', third='third 1'),
            dict(first='first 2', second='second 2', third='third 2'),
        ])
    
    def test_can_run_feature_with_hashes_in_background_step(self):
        @step('step with hashes')
        def step_with_hashes(step):
            world.hashes = step.hashes
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
        world.hashes = None
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(1)
        result.wasSuccessful() |should| be(True)
        world.hashes |should| each_be_equal_to([
            dict(first='first 1', second='second 1', third='third 1'),
            dict(first='first 2', second='second 2', third='third 2'),
        ])
    
    def test_can_run_feature_with_scenario_outline_and_examples(self):
        @step('a (.*) with (.*)')
        def a_key_with_value(step, key, value):
            world.run.append((key, value))
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario Outline: follows
            Given a <key> with <value>
          Examples:
            | key   | value     |
            | key 1 | value 1   |
            | key 2 | value 2   |
        ''')
        world.run = []
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        world.run |should| each_be_equal_to([
            ('key 1', 'value 1'),
            ('key 2', 'value 2'),
        ])
    
    def test_can_run_feature_with_scenario_outline_with_multiline(self):
        @step('a multiline')
        def a_multiline(step):
            world.run.append(step.multiline)
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
        world.run = []
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        world.run |should| each_be_equal_to([
            'with first\n',
            'with second\n',
        ])
    
    def test_can_run_feature_with_scenario_outline_with_hashes(self):
        @step('a hash')
        def a_hash(step):
            world.run.append(list(step.hashes))
        feature = load_feature('''
        Feature: with multiline scenarnio
          Scenario Outline: follows
            Given a hash
              | <key>   | value         |
              | the     | <placeholder> |
          Examples:
            | <key>   | <placeholder> |
            | key       | first         |
            | but       | second        |
        ''')
        world.run = []
        result = unittest.TestResult()
        feature.run(result)
        result.testsRun |should| be(2)
        result.wasSuccessful() |should| be(True)
        world.run |should| each_be_equal_to([
            [dict(key='the', value='first')],
            [dict(but='the', value='second')],
        ])


#.............................................................................
#   test_feature.py
