# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_scenario.py --- Wishes scenario vows
#=============================================================================
import unittest

import mock
from should_dsl import should

from wishes.feature import Scenario, step, StepDefinition, world


class ScenarioTest(unittest.TestCase):
    
    def setUp(self):
        StepDefinition.clear()
    
    @mock.patch('wishes.feature.FeatureTest')
    def test_gets_itself_skipped_if_without_steps(self, FeatureTest):
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        scenario.run(feature)
        len(feature.method_calls) |should| be(1)
        feature.skipTest |should| be_called_once_with('no steps defined')
    
    def test_can_add_steps(self):
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'there is a step')
        scenario.step_count |should| be(1)
    
    def test_knows_number_of_undefined_steps(self):
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'there is a step')
        scenario.step_count_undefined |should| be(1)

    def test_knows_number_of_defined_steps(self):
        @step('there is a step')
        def there_is_a_step(step):
            pass
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'there is a step')
        scenario.step_count_defined |should| be(1)

    @mock.patch('wishes.feature.FeatureTest')
    def test_can_run_step(self, FeatureTest):
        @step('there is a step')
        def there_is_a_step(step):
            self.run_count += 1
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'there is a step')
        self.run_count = 0
        scenario.run(feature)
        self.run_count |should| be(1)

    @mock.patch('wishes.feature.FeatureTest')
    def test_can_run_steps(self, FeatureTest):
        @step('there is step ([0-9]+)')
        def there_is_step_number(step, number):
            world.steps_run.append(int(number))
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        for i in range(3):
            scenario.add_step('Given', 'there is step %d' % i)
        world.steps_run = []
        scenario.run(feature)
        world.steps_run |should| each_be_equal_to(range(3))

    @mock.patch('wishes.feature.FeatureTest')
    def test_stops_at_the_first_undefined_step(self, FeatureTest):
        @step('there is step ([0-9]+)')
        def there_is_step_number(step, number):
            world.steps_run.append(int(number))
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        for i in range(3):
            scenario.add_step('Given', 'there is step %d' % i)
        scenario.add_step('And', 'there is an undefined step')
        scenario.add_step('Given', 'there is step %d' % 4)
        world.steps_run = []
        scenario.run(feature)
        world.steps_run |should| each_be_equal_to(range(3))

    def test_can_add_multiline_step(object):
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'multiline', multilines=['line\n'])
        scenario.step_count |should| be(1)
        scenario.steps[0].multilines |should| be_equal_to(['line\n'])

#.............................................................................
#   test_scenario.py
