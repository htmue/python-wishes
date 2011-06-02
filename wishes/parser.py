# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   parser.py --- Parse features
#=============================================================================
import os.path
import re
import sys
from cStringIO import StringIO

import yaml

from compat import combinations_with_replacement


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
            if pattern is None:
                matcher = None
            else:
                try:
                    pattern = self.patterns[pattern]
                except KeyError:
                    matcher = getattr(self, pattern)
                else:
                    matcher = pattern.match
            transitions = tuple(getattr(self, method) for method in transitions)
            yield matcher, transitions, next_state
    
    def _compile_patterns(self, patterns):
        for key, value in patterns.iteritems():
            yield key, re.compile(value)
    
    @classmethod
    def parser_info(cls):
        events = set()
        states = set()
        matchers = set()
        for state, transitions in cls.config['states'].items():
            for matcher, _, _ in transitions:
                states.add(state)
                matchers.add(matcher)
                events.add((state, matcher))
        return events, states, matchers
    
    @classmethod
    def parser_transitions(cls):
        states = set()
        reachable_transitions = set()
        for state, transitions in cls.config['states'].items():
            for _, _, target in transitions:
                states.add(state)
                reachable_transitions.add((state, target))
        possible_transitions = set(combinations_with_replacement(states, 2))
        return reachable_transitions, possible_transitions
    
    @classmethod
    def dump_unreachable_transitions(cls, stream=sys.stdout):
        reachable_transitions, possible_transitions = Parser.parser_transitions()
        unreachable_transitions = possible_transitions - reachable_transitions
        unreachable_transitions = sorted(list(t) for t in unreachable_transitions)
        yaml.dump(unreachable_transitions, stream=stream)
    
    def parse(self, stream):
        self.start_parse(stream)
        self.current_state = 'start'
        for line in self.stream:
            self.handle_line(line)
        self.handle_line(None)
        self.finish_parse()
    
    def is_whitespace(self, line):
        if line is not None:
            match = self.whitespace_pattern.match(line)
            if match:
                self.match = match
                return True
    
    def handle_line(self, line):
        new_states = self.states[self.current_state]
        for matcher, transitions, next_state in new_states:
            if matcher is None or line is None:
                match = matcher is line
            else:
                match = matcher(line)
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
    
    def start_background(self):
        self.handler.start_background(*self.stripped_groups())
    
    def finish_background(self):
        self.handler.finish_background()
    
    def start_outline(self):
        self.handler.start_outline(*self.stripped_groups())
    
    def finish_outline(self):
        self.handler.finish_outline()
    
    def start_examples(self):
        self.handler.start_examples(*self.stripped_groups())
    
    def finish_examples(self):
        self.handler.finish_examples()
    
    def start_step(self):
        self.handler.start_step(*self.stripped_groups())
    
    def finish_step(self):
        self.handler.finish_step()
    
    def start_description(self):
        self.handler.start_description()
    
    def finish_description(self):
        self.handler.finish_description()
    
    def data(self):
        self.handler.data(*self.stripped_groups())
    
    def comment(self):
        self.handler.comment(self.match.string.lstrip())
    
    def whitespace(self):
        self.handler.whitespace(self.match.string)
    
    def start_multiline(self):
        self.multiline_indent = self.get_multiline_indent(self.match)
        self.handler.start_multiline(self.multiline_indent)
    
    def finish_multiline(self):
        self.multiline_indent = None
        self.handler.finish_multiline()
    
    def multiline_end(self, line):
        match = self.patterns['multiline'].match(line)
        if match and self.get_multiline_indent(match) == self.multiline_indent:
            return match
    
    def get_multiline_indent(self, match):
        multiline_start = match.group(1)
        return len(multiline_start) - len(multiline_start.lstrip())
    
    def multiline_data(self):
        line = self.match.string
        if line[:self.multiline_indent].strip():
            raise ParseError('invalid dedent in multiline: %r', line)
        self.handler.data(line[self.multiline_indent:])
    
    def start_hash(self):
        self.handler.start_hash(*self.get_hash_line_parts())
    
    def finish_hash(self):
        self.handler.finish_hash()
    
    def hash_line(self):
        self.handler.hash_data(*self.get_hash_line_parts())
    
    def get_hash_line_parts(self):
        line = self.match.group(1).rstrip('|')
        return tuple(part.strip() for part in line.split('|'))
    
    def tags(self):
        tags = tuple(tag[1:] for tag in self.match.group(1).strip().split())
        self.handler.tags(*tags)
    
    def stripped_groups(self):
        return tuple(arg.strip() for arg in self.match.groups())


class LogHandler(object):
    
    def __getattr__(self, key):
        def log(*args):
            print '%s:%s' % (key, args)
        return log

#.............................................................................
#   parser.py
