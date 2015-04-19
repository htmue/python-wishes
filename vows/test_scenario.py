# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_scenario.py --- Wishes scenario vows
#=============================================================================
from __future__ import unicode_literals

from functools import partial

import mock
from should_dsl import should

from wishes.compat import unittest
from wishes.feature import Scenario, step, StepDefinition, StepDefinitionError


class ScenarioVows(unittest.TestCase):
    
    def setUp(self):
        StepDefinition.clear()
    
    @mock.patch('wishes.feature.FeatureTest')
    def test_gets_itself_skipped_if_without_steps(self, FeatureTest):
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        scenario.run(feature)
        len(feature.method_calls) |should| be(1)
        feature.skipTest.assert_called_once_with('no steps defined')
    
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
            steps_run.append(int(number))
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        for i in range(3):
            scenario.add_step('Given', 'there is step %d' % i)
        steps_run = []
        scenario.run(feature)
        steps_run |should| each_be_equal_to(range(3))
    
    @mock.patch('wishes.feature.FeatureTest')
    def test_stops_at_the_first_undefined_step(self, FeatureTest):
        @step('there is step ([0-9]+)')
        def there_is_step_number(step, number):
            steps_run.append(int(number))
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        for i in range(3):
            scenario.add_step('Given', 'there is step %d' % i)
        scenario.add_step('And', 'there is an undefined step')
        scenario.add_step('Given', 'there is step %d' % 4)
        steps_run = []
        scenario.run(feature)
        steps_run |should| each_be_equal_to(range(3))
    
    def test_can_add_multiline_step(self):
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'multiline', multilines=['line\n'])
        scenario.step_count |should| be(1)
        scenario.steps[0].multilines |should| be_equal_to(['line\n'])
    
    def test_can_add_hashes_step(self):
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'hashes', hashes=[dict(key='value')])
        scenario.step_count |should| be(1)
        scenario.steps[0].hashes |should| be_equal_to([dict(key='value')])
    
    def test_can_be_created_from_outline_and_hash(self):
        outline = Scenario('Test outline')
        outline.add_step('Given', 'a value <value>')
        scenario = Scenario('Test scenario', outline=(outline, {'<value>': 'unique'}))
        scenario.step_count |should| be(1)
        step = scenario.steps[0]
        step.kind |should| be_equal_to('Given')
        step.text |should| be_equal_to('a value unique')
    
    def test_can_be_created_from_outline_background_and_hash(self):
        background = Scenario('Test background')
        background.add_step('Given', 'a value <value>')
        outline = Scenario('Test outline', background=background)
        outline.add_step('Given', 'another value')
        scenario = Scenario('Test scenario', outline=(outline, {'<value>': 'unique'}))
        scenario.background.step_count |should| be(1)
        step = scenario.background.steps[0]
        step.kind |should| be_equal_to('Given')
        step.text |should| be_equal_to('a value unique')
        scenario.step_count |should| be(1)
        step = scenario.steps[0]
        step.kind |should| be_equal_to('Given')
        step.text |should| be_equal_to('another value')
    
    def test_raises_exception_when_multiple_step_definitions_match(self):
        @step('is step ([0-9]+)')
        def is_step_number(step, number):
            pass
        @step('is step (.+)')
        def is_step_any(step, any):
            pass
        scenario = Scenario('Test scenario')
        add_step = partial(scenario.add_step, 'Given', 'there is step 1')
        add_step |should| throw(StepDefinitionError)
    
    @mock.patch('wishes.feature.FeatureTest')
    def test_displays_pending_steps_in_skip_reason(self, FeatureTest):
        feature = FeatureTest()
        scenario = Scenario('Test scenario')
        scenario.add_step('Given', 'there is a step')
        scenario.run(feature)
        feature.skipTest.assert_called_once_with('pending 1 step(s): [<Given there is a step>]')
    
    def test_can_be_created_with_tags(self):
        tags = ['wip', 'fast']
        scenario = Scenario('Test scenario', tags=tags)
        scenario.tags |should| each_be_equal_to(tags)

#.............................................................................
#   test_scenario.py
