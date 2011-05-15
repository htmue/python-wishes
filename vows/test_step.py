# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_step.py --- Wishes step vows
#=============================================================================
import unittest

from should_dsl import should

from wishes.feature import Step, step, StepDefinition, world


class StepTest(unittest.TestCase):

    def setUp(self):
        StepDefinition.clear()
    
    def test_can_be_created(self):
        step = Step('Given', 'there is a step')
    
    def test_knows_if_it_is_undefined(self):
        step = Step('Given', 'there is a step')
        step.is_undefined |should| be(True)

    def test_knows_if_it_is_defined(self):
        @step('there is a step')
        def there_is_a_step(step):
            pass
        step_ = Step('Given', 'there is a step')
        step_.is_defined |should| be(True)

    def test_can_run_if_defined(self):
        @step('there is a step')
        def there_is_a_step(step):
            world.run_count += 1
        step_ = Step('Given', 'there is a step')
        world.run_count = 0
        step_.run()
        world.run_count |should| be(1)
    
    def test_passes_capture_groups_to_definition(self):
        @step('this is (.*)')
        def this_is_captured(step, capture):
            world.capture = capture
        step_ = Step('Given', 'this is captured')
        world.capture = None
        step_.run()
        world.capture |should| be_equal_to('captured')

#.............................................................................
#   test_step.py
