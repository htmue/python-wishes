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

#.............................................................................
#   test_feature.py
