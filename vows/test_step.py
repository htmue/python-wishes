# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_step.py --- Wishes step vows
#=============================================================================
from should_dsl import should

from wishes.compat import unittest
from wishes.feature import Step, step, StepDefinition, world, Hashes


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
    
    def test_can_fill_itself_from_example(self):
        outline_step = Step('Given', 'an <outlined> step')
        filled_step = outline_step.fill_from_example({'<outlined>': 'filled'})
        filled_step.text |should| be_equal_to('an filled step')
    
    def test_can_fill_its_multiline_from_example(self):
        outline_step = Step('Given', 'a step', multilines=['with <placeholder>\n'])
        filled_step = outline_step.fill_from_example({'<placeholder>': 'replacement'})
        filled_step.multiline |should| be_equal_to('with replacement\n')
    
    def test_can_fill_its_hashes_from_example(self):
        hashes = Hashes(keys=('key', '<key>'), values=[('<value>', 'value')])
        outline_step = Step('Given', 'a step', hashes=hashes)
        filled_step = outline_step.fill_from_example({'<key>': 'a key', '<value>': 'a value'})
        filled_step.hashes |should| each_be_equal_to([
            {'a key': 'value', 'key': 'a value'},
        ])


class HashesTest(unittest.TestCase):
    
    def test_maps_values_to_keys(self):
        hash = Hashes(('first', 'second'), [
            ('first 1', 'second 1'),
            ('first 2', 'second 2'),
        ])
        list(hash) |should| each_be_equal_to([
            dict(first='first 1', second='second 1'),
            dict(first='first 2', second='second 2'),
        ])
    
    def test_fixes_keys_for_outline(self):
        hash = Hashes(('first', 'second'), [
            ('first 1', 'second 1'),
            ('first 2', 'second 2'),
        ])
        hash.fix_keys_for_outline()
        list(hash) |should| each_be_equal_to([
            {'<first>': 'first 1', '<second>': 'second 1'},
            {'<first>': 'first 2', '<second>': 'second 2'},
        ])
    
    def test_does_not_fix_keys_that_do_not_need_to_be_fixed(self):
        hash = Hashes(('<first>', '[second]', '{third}', '(fourth)'), [range(4)])
        hash.fix_keys_for_outline()
        list(hash) |should| each_be_equal_to([
            {'<first>': 0, '[second]': 1, '{third}': 2, '(fourth)': 3}
        ])

#.............................................................................
#   test_step.py
