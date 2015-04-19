# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   test_parser.py --- Wishes parser vows
#=============================================================================
from __future__ import unicode_literals

import os.path
import re
from functools import partial

import mock
import six
import yaml
from should_dsl import should
from io import StringIO

from wishes.compat import unittest
from wishes.parser import Parser, ParseError


test_data = yaml.load(open(os.path.splitext(__file__)[0] + '.yaml'))

class ParserCallbackVowsMeta(type):
    
    def __new__(self, classname, bases, classdict):
        for key, test in six.iteritems(test_data['callbacks']):
            if 'input' in test and 'callbacks' in test:
                define_method(classdict, test, 'test_can_' + key.replace(' ', '_'))
        return type.__new__(self, classname, bases, classdict)

def define_method(classdict, test, test_name):
    def runTest(self):
        parse_log_check(six.text_type(test['input']), test['callbacks'])
    runTest.__name__ = str(test_name)
    classdict[test_name] = runTest

def parse_log_check(input, callbacks):
    handler = mock.Mock()
    parser = Parser(handler)
    try:
        parser.parse(input.strip())
    except ParseError:
        handler.parse_error()
    method_calls = [(name, tuple(args), kwargs) for name, args, kwargs in callbacks]
    handler.method_calls |should| each_be_equal_to(method_calls)


@six.add_metaclass(ParserCallbackVowsMeta)
class ParserVows(unittest.TestCase):
    
    def test_can_parse_filelikes(self):
        parser = Parser()
        parser.parse(StringIO())
    
    def test_can_parse_strings(self):
        parser = Parser()
        parser.parse('')
    
    def test_raises_parse_error_on_invalid_multiline_dedent(self):
        handler = mock.Mock()
        parser = Parser(handler)
        
        parse = partial(parser.parse, '''
        Feature: invalid multiline dedent
          Scenario: with multiline step
            Given an invalid multiline:
              """
            dedented
              """
        '''.strip())
        parse |should| throw(ParseError)
    
    @unittest.skip('pending review')
    def test_containes_unreachable_transitions(self):
        reachable_transitions, possible_transitions = Parser.parser_transitions()
        unreachable_transitions = possible_transitions - reachable_transitions
        unreachable_transitions = set(t for t in unreachable_transitions)
        confirmed = set(tuple(t) for t in test_data['unreachable transitions'])
        non_confirmed = unreachable_transitions - confirmed
        print(non_confirmed)
        sorted(non_confirmed) |should| each_be_equal_to([])


#.............................................................................
#   test_parser.py
