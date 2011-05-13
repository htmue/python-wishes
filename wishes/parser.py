# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   parser.py --- Parse features
#=============================================================================
import os.path
import re
from cStringIO import StringIO

import yaml


class ParseError(Exception):
    pass

class Parser(object):
    config = yaml.load(open(os.path.splitext(__file__)[0] + '.yaml'))
    
    def __init__(self, handler=None):
        self.handler = LogHandler() if handler is None else handler
        self.patterns = dict(self._compile_patterns(self.config['patterns']))
        self.whitespace_pattern = self.patterns['whitespace']
        self.states = dict(self._compile_states(self.config['states']))
        self.multiline_indent = None
        self.current_state = None

    def _compile_states(self, states):
        for key, rows in states.iteritems():
            yield key, tuple(self._compile_transitions(rows))
    
    def _compile_transitions(self, rows):
        for pattern, transitions, next_state in rows:
            if pattern is not None:
                pattern = self.patterns[pattern]
            transitions = tuple(getattr(self, method) for method in transitions)
            yield pattern, transitions, next_state
    
    def _compile_patterns(self, patterns):
        for key, value in patterns.iteritems():
            yield key, re.compile(value)
    
    def parse(self, stream):
        self.start_parse(stream)
        self.current_state = 'start'
        for line in self.stream:
            self.handle_line(line)
        self.handle_line(None)
        self.finish_parse()

    def is_whitespace(self, line):
        return line is not None and self.whitespace_pattern.match(line)
    
    def handle_line(self, line):
        new_states = self.states[self.current_state]
        for pattern, transitions, next_state in new_states:
            if pattern is None or line is None:
                match = pattern is line
            else:
                match = pattern.match(line)
            if match:
                self.match = match
                for transition in transitions:
                    transition()
                self.current_state = next_state
                return
        if self.is_whitespace(line):
            self.whitespace()
            return
        expected = [row[0] for row in self.config['states'][self.current_state]]
        raise ParseError('unexpected line %r in %r, expected on of %s' % (line, self.current_state, expected))
    
    def start_parse(self, stream):
        if isinstance(stream, basestring):
            self.stream = StringIO(stream)
        else:
            self.stream = stream
        try:
            name = stream.name
        except AttributeError:
            name = '<string>'
        self.handler.start_parse(name)

    def finish_parse(self):
        self.handler.finish_parse()
    
    def start_feature(self):
        self.handler.start_feature(*self.stripped_groups())

    def finish_feature(self):
        self.handler.finish_feature()

    def start_scenario(self):
        self.handler.start_scenario(*self.stripped_groups())

    def finish_scenario(self):
        self.handler.finish_scenario()

    def start_step(self):
        self.handler.start_step(*self.stripped_groups())

    def finish_step(self):
        self.handler.finish_step()

    def start_feature_description(self):
        self.handler.start_feature_description()

    def finish_feature_description(self):
        self.handler.finish_feature_description()
    
    def data(self):
        self.handler.data(*self.stripped_groups())
    
    def whitespace(self):
        self.handler.whitespace(self.match.string)
    
    def start_multiline(self):
        multiline_start = self.match.group(1)
        self._multiline_indent = len(multiline_start) - len(multiline_start.lstrip())
        self.handler.start_multiline(self._multiline_indent)
    
    def finish_multiline(self):
        self._multiline_indent = None
        self.handler.finish_multiline()
    
    def multiline_data(self):
        self.handler.data(self.match.string[self._multiline_indent:])
        

    def stripped_groups(self):
        return tuple(arg.strip() for arg in self.match.groups())


class LogHandler(object):
    
    def __getattr__(self, key):
        def log(*args):
            print '%s:%s' % (key, args)
        return log

#.............................................................................
#   parser.py
