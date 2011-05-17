# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   test_parser.py --- Wishes parser vows
#=============================================================================
import os.path
import unittest
from cStringIO import StringIO
from functools import partial

import mock
import yaml
from should_dsl import should

from wishes.parser import Parser, ParseError


test_data = yaml.load(open(os.path.splitext(__file__)[0] + '.yaml'))

class ParserCallbackVowsMeta(type):
    
    def __new__(self, classname, bases, classdict):
        for key, test in test_data['callbacks'].iteritems():
            if 'input' in test and 'callbacks' in test:
                define_method(classdict, test, 'test_' + key.replace(' ', '_'))
        return type.__new__(self, classname, bases, classdict)

def define_method(classdict, test, test_name):
    def runTest(self):
        parse_log_check(test['input'], test['callbacks'])
    runTest.__name__ = test_name
    classdict[test_name] = runTest

def parse_log_check(input, callbacks):
    handler = mock.Mock()
    parser = Parser(handler)
    parser.parse(input.strip())
    method_calls = [(name, tuple(args), kwargs) for name, args, kwargs in callbacks]
    handler.method_calls |should| each_be_equal_to(method_calls)


class ParserVows(unittest.TestCase):
    __metaclass__ = ParserCallbackVowsMeta
    
    def test_can_parse_filelikes(self):
        parser = Parser()
        parser.parse(StringIO())
    
    def test_can_parse_strings(self):
        parser = Parser()
        parser.parse('')
    
    def test_reports_start_and_end(self):
        handler = mock.Mock()
        features = StringIO()
        parser = Parser(handler)
        
        parser.parse(features)
        
        handler.method_calls |should| each_be_equal_to([
            ('start_parse', ('<string>',), {}),
            ('finish_parse', (), {}),
        ])
    
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

    def test_tested_parsing_events_are_complete(self):
        events, states, matchers = Parser.parser_info()
        tested_events = set()
        for test in test_data['callbacks'].values():
            for state, matcher in test['tested_events']:
                state |should| be_in(states)
                matcher |should| be_in(matchers)
                tested_events.add((state, matcher))
        untested_events = events - tested_events
        sorted(untested_events) |should| each_be_equal_to([])

    def test_containes_unreachable_transitions(self):
        reachable_transitions, possible_transitions = Parser.parser_transitions()
        unreachable_transitions = possible_transitions - reachable_transitions
        unreachable_transitions = sorted(list(t) for t in unreachable_transitions)
        unreachable_transitions |should| each_be_equal_to(test_data['unreachable transitions'])

#.............................................................................
#   test_parser.py
