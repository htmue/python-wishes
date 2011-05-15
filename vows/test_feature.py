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
        run |should| each_be_equal_to((True, True, False))
        

#.............................................................................
#   test_feature.py
