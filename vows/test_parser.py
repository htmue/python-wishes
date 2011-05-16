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


class ParserCallbackVowsMeta(type):
    feature_callbacks_data = yaml.load(open(os.path.join(os.path.dirname(__file__), 'test_parser_callbacks.yaml')))
    
    def __new__(self, classname, bases, classdict):
        for key, data in self.feature_callbacks_data.iteritems():
            define_method(classdict, data, 'test_' + key.replace(' ', '_'))
        return type.__new__(self, classname, bases, classdict)

def define_method(classdict, data, test_name):
    def runTest(self):
        parse_log_check(**data)
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


#.............................................................................
#   test_parser.py
