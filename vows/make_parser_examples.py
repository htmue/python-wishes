# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-06-02.
#=============================================================================
#   make_parser_examples.py --- Create parser test_parser.yaml data.
#
#  test_parser.yaml should be re-created and inspected manually after each
#  change in parser.(py|yaml)
#=============================================================================
import os.path
import re
import sys

import mock
import yaml

from wishes.parser import Parser, ParseError


transitions = yaml.load(open(os.path.splitext(__file__)[0] + '.yaml'))
placeholder_re = re.compile(r'\{[^}]*\}')

def placeholder_count(string):
    return len(placeholder_re.findall(string))

def fill(names, lines):
    if isinstance(lines, list):
        for line in lines:
            for filled in fill(names, line):
                yield filled
    else:
        count = placeholder_count(lines)
        if count == 0:
            string = lines
        elif count == 1:
            string = lines.format(names.next())
        elif count > 1:
            string = lines.format(*tuple(names.next().split()[-count:]))
        yield string

def generate_names(name):
    for i in xrange(sys.maxint):
        yield '{} {}'.format(name, chr(ord('a') + i))

def make_feature_examples(name, state, matcher):
    names = generate_names(name)
    setup_lines = list(fill(names, transitions['setup'][state]))
    finish = transitions['finish'].get(matcher, {})
    finish_lines = []
    for key in state, 'any':
        if key in finish:
            finish_lines = list(fill(names, finish[key]))
            break
    events = transitions['events'][matcher]
    matcher_lines = [list(fill(names, line)) for line in events]
    for lines in matcher_lines:
        yield len(events), ''.join(setup_lines + lines + finish_lines)

def make_examples():
    events, states, matchers = Parser.parser_info()
    skip = set(map(tuple, transitions['skip']))
    for state in sorted(states):
        for matcher in sorted(matchers):
            event = state, matcher
            if not event in skip:
                success = event in events
                name = 'handle {} in {}'.format(matcher, state)
                for i, (n, example) in enumerate(make_feature_examples(name, state, matcher)):
                    yield name, n, i, success, example
            
def run_example(input, success):
    handler = mock.Mock()
    parser = Parser(handler)
    try:
        parser.parse(input.strip())
    except ParseError as e:
        handler.parse_error()
        if success:
            raise
    else:
        if not success:
            raise RuntimeError('exception expected')
    return [[name, list(args), kwargs] for name, args, kwargs in handler.method_calls]

def main():
    print 'callbacks:'
    for name, n, i, success, example in make_examples():
        if n > 1:
            name = '{} {}'.format(name, i + 1)        
        print
        print '  {}:'.format(name)
        print '    success: {}'.format(str(success).lower())
        print '    input: |'
        for line in example.splitlines():
            print '      {}'.format(line)
        print
        method_calls = run_example(example, success)
        if method_calls is not None:
            print '    callbacks:'
            for c in method_calls:
                dump = yaml.dump(c, default_flow_style=True).strip()
                print '    - {}'.format(dump)
    print
    print 'unreachable transitions:'
    Parser.dump_unreachable_transitions()

if __name__ == '__main__':
    import datetime
    print '''\
# -*- coding:utf-8 -*-
# Autogenerated on {}.
#=============================================================================
#   test_parser.yaml --- Wishes parser vows, data driven
#=============================================================================
'''.format(datetime.date.today())
    main()
    print '''
#.............................................................................
#   test_parser.yaml'''

#.............................................................................
#   make_parser_examples.py