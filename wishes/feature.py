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
    def add_scenario(self, methodName, scenario):
        setattr(self, methodName, self.runTest)
        self.scenarios[methodName] = scenario


class Scenario(object):
    
    def __init__(self, title, background=None):
        self.title = title
        self.background = background
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

    def add_step(self, kind, text):
        self.steps.append(Step(kind, text))

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
    
    def __init__(self, kind, text):
        self.kind = kind
        self.text = text
        self.definition, self.match = StepDefinition.get_step_definition(kind, text)
    
    @property
    def is_defined(self):
        return self.definition is not None

    @property
    def is_undefined(self):
        return self.definition is None

    def run(self):
        self.definition(self)


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
