# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   feature.py --- Feature test case
#=============================================================================
import re
import threading

class FeatureTest(object):
    scenarios = dict()
    
    def runTest(self):
        if self.is_empty:
            self.skipTest('no scenarios defined')
        self.scenario.run(self)
    
    @property
    def is_empty(self):
        return self._testMethodName == 'runTest'
    
    @property
    def scenario(self):
        return self.scenarios[self._testMethodName]
    
    @classmethod
    def add_scenario(cls, methodName, scenario):
        setattr(cls, methodName, cls.runTest)
        cls.scenarios[methodName] = scenario


def fill_from_example(string, example):
    for key, value in example.iteritems():
        string = string.replace(key, value)
    return string

class Hashes(object):
    BRACKETS = (
        re.compile(r'<.*>$'),
        re.compile(r'\[.*\]$'),
        re.compile(r'\(.*\)$'),
        re.compile(r'\{.*\}$'),
    )
    
    def __init__(self, keys=None, values=None):
        self.keys = () if keys is None else keys
        self.values = [] if values is None else values
    
    def add_row(self, row):
        self.values.append(row)
    
    def fix_keys_for_outline(self):
        self.keys = [self.fix_key_for_outline(key) for key in self.keys]
    
    def fix_key_for_outline(self, key):
        for bracket_re in self.BRACKETS:
            if bracket_re.match(key):
                return key
        return '<%s>' % key
    
    def fill_from_example(self, example):
        return Hashes(
            keys=[fill_from_example(key, example) for key in self.keys],
            values=[
                [fill_from_example(value, example) for value in row]
                for row in self.values
            ],
        )
    
    def __len__(self):
        return len(self.values)
    
    def __iter__(self):
        for row in self.values:
            yield dict(zip(self.keys, row))


class Scenario(object):
    
    def __init__(self, title=None, background=None, outline=None):
        self.background = background
        if outline is not None:
            self.outline, self.example = outline
            self.title = fill_from_example(self.outline.title, self.example)
            self.create_steps_from_outline()
        else:
            self.title = title
            self.steps = []
    
    def run(self, feature):
        if not self.steps:
            feature.skipTest('no steps defined')
        if self.background is not None:
            self.background.run(feature)
        for step in self.steps:
            if step.is_undefined:
                feature.skipTest('pending %d step(s)' % self.step_count_undefined)
                return
            step.run()
    
    def add_step(self, kind, text, multilines=None, hashes=None):
        self.steps.append(Step(kind, text, multilines=multilines, hashes=hashes))
    
    def create_steps_from_outline(self):
        self.steps = list(self.outline.create_steps_from_example(self.example))
    
    def create_steps_from_example(self, example):
        for step in self.steps:
            yield step.fill_from_example(example)
    
    @property
    def step_count(self):
        return len(self.steps)
    
    @property
    def step_count_defined(self):
        return len(self.defined_steps)
    
    @property
    def step_count_undefined(self):
        return len(self.undefined_steps)
    
    @property
    def defined_steps(self):
        return filter(lambda step: step.is_defined, self.steps)
    
    @property
    def undefined_steps(self):
        return filter(lambda step: step.is_undefined, self.steps)


class Step(object):
    
    def __init__(self, kind, text, multilines=None, hashes=None):
        self.kind = kind
        self.text = text
        self.definition, self.match = StepDefinition.get_step_definition(kind, text)
        self.multilines = [] if multilines is None else multilines
        self.hashes = Hashes() if hashes is None else hashes
    
    @property
    def is_defined(self):
        return self.definition is not None
    
    @property
    def is_undefined(self):
        return self.definition is None
    
    @property
    def multiline(self):
        return ''.join(self.multilines)
    
    def run(self):
        self.definition(self)
    
    def fill_from_example(self, example):
        multilines = [fill_from_example(line, example) for line in self.multilines]
        return Step(self.kind, fill_from_example(self.text, example),
            multilines=multilines, hashes=self.hashes.fill_from_example(example))


class StepDefinition(object):
    step_definitions = []
    
    def __init__(self, pattern, definition):
        self.pattern = re.compile(pattern)
        self.definition = definition
        self.add_step_definition(self)
    
    @classmethod
    def add_step_definition(self, step_definition):
        self.step_definitions.append(step_definition)
    
    @classmethod
    def get_step_definition(self, kind, text):
        s = ' '.join((kind, text))
        for step_definition in self.step_definitions:
            match = step_definition.match(s)
            if match:
                return step_definition, match
        return None, None
    
    @classmethod
    def clear(self):
        self.step_definitions = []
    
    def match(self, s):
        return self.pattern.search(s)
    
    def __call__(self, step):
        self.definition(step, *step.match.groups())


def define_step(pattern, definition):
    StepDefinition(pattern, definition)

def step(pattern):
    def step_definition(definition):
        StepDefinition(pattern, definition)
        return definition
    return step_definition


class World(threading.local):
    pass

world = World()

#.............................................................................
#   feature.py
