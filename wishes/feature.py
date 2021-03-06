# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   feature.py --- Feature test case
#=============================================================================
from __future__ import unicode_literals

import re
import threading
import inspect

import six


try:
    from autocheck.tags import add_tags, get_tags
except ImportError:
    add_tags = get_tags = None

__unittest = True

class World(threading.local):
    def __init__(self, feature=None):
        self.feature = feature


class FeatureTest(object):
    scenarios = dict()
    _world = None
    
    def __init__(self, *args, **kwargs):
        super(FeatureTest, self).__init__(*args, **kwargs)
        if add_tags is not None and not self.is_empty and self.scenario.tags is not None:
            add_tags(self, self.scenario.tags)
    
    def runTest(self):
        if self.is_empty:
            self.skipTest('no scenarios defined')
        self.scenario.run(self)
    
    def run(self, result=None):
        self.result = result
        self.current_tags = getattr(result, 'tags', None)
        super(FeatureTest, self).run(result)
    
    def shortDescription(self):
        if self.is_empty:
            return 'Feature: {0}'.format(self.title)
        else:
            return 'Scenario: {0}'.format(self.scenario.title)
    
    @property
    def world(self):
        if self._world is None:
            self._world = getattr(self, 'World', World)(self)
        return self._world
    
    @property
    def is_empty(self):
        return self._testMethodName == 'runTest'
    
    @property
    def scenario(self):
        return self.scenarios[self._testMethodName]
    
    @property
    def is_scenario(self):
        return not self.is_empty
    
    @classmethod
    def add_scenario(cls, methodName, scenario):
        setattr(cls, methodName, cls.runTest)
        cls.scenarios[methodName] = scenario
    
    def getsource(self):
        return self.shortDescription() if self.is_empty else self.scenario.getsource()


def fill_from_example(string, example):
    for key, value in six.iteritems(example):
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
    
    def __init__(self, title=None, background=None, outline=None, tags=None):
        self.background = background
        self.tags = tags
        self.add_tags_from_parent(background)
        if outline is not None:
            self.outline, self.example = outline
            background_outline = self.outline.background
            if background_outline is not None:
                self.background = Scenario(
                    title=background_outline.title,
                    outline=(background_outline, self.example),
                )
            self.title = fill_from_example(self.outline.title, self.example)
            self.create_steps_from_outline()
            self.add_tags_from_parent(self.outline)
        else:
            self.title = title
            self.steps = []
    
    def add_tags_from_parent(self, parent):
        if parent is not None and parent.tags is not None:
            if self.tags is None:
                self.tags = parent.tags
            else:
                self.tags = set(self.tags) | parent.tags
    
    def run(self, feature):
        if not self.steps:
            feature.skipTest('no steps defined')
        if self.background is not None:
            self.background.run(feature)
        startStep = getattr(feature.result, 'startStep', None)
        addStepSuccess = getattr(feature.result, 'addStepSuccess', None)
        addStepFailure = getattr(feature.result, 'addStepFailure', None)
        addStepError = getattr(feature.result, 'addStepError', None)
        addStepUndefined = getattr(feature.result, 'addStepUndefined', None)
        stopStep = getattr(feature.result, 'stopStep', None)
        for step in self.steps:
            if startStep is not None:
                startStep(step)
            if step.is_undefined:
                if addStepUndefined is not None:
                    addStepUndefined(step)
                if stopStep is not None:
                    stopStep(step)
                feature.skipTest('pending %d step(s): %s' % (self.step_count_undefined, self.undefined_steps))
                return
            try:
                step.world = feature.world
                step.run()
                step.world = None
            except feature.failureException:
                if addStepFailure is not None:
                    addStepFailure(step)
                raise
            except Exception:
                if addStepError is not None:
                    addStepError(step)
                raise
            else:
                if addStepSuccess is not None:
                    addStepSuccess(step)
            finally:
                if stopStep is not None:
                    stopStep(step)
    
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
        return list(filter(lambda step: step.is_defined, self.steps))
    
    @property
    def undefined_steps(self):
        return list(filter(lambda step: step.is_undefined, self.steps))

    def getsourcebits(self):
        if self.background is not None:
            for bit in self.background.getsourcebits():
                yield bit
        yield unicode(self.title)
        for step in self.steps:
            for bit in step.getsourcebits():
                yield bit

    def getsource(self):
        return u'\n'.join(self.getsourcebits()).encode('utf-8')


@six.python_2_unicode_compatible
class Step(object):
    
    def __init__(self, kind, text, multilines=None, hashes=None):
        self.kind = kind
        self.text = text
        self.definition, self.match = StepDefinition.get_step_definition(kind, text)
        self.multilines = [] if multilines is None else multilines
        self.hashes = Hashes() if hashes is None else hashes
    
    def __str__(self):
        return ('%s %s' % (self.kind, self.text))
    
    def __repr__(self):
        return '<%s>' % self
    
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
    
    def getsourcebits(self):
        yield unicode(self)
        for line in self.multilines:
            yield line
        if self.hashes:
            yield u'|'.join(self.hashes.keys)
            for line in self.hashes.values:
                yield u'|'.join(line)

class StepDefinitionError(Exception):
    pass

class StepDefinition(object):
    step_definitions = []
    
    def __init__(self, pattern, definition):
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.definition = definition
        self.add_step_definition(self)
    
    def __repr__(self):
        return repr(self.pattern.pattern)
    
    @classmethod
    def add_step_definition(cls, step_definition):
        cls.step_definitions.append(step_definition)
    
    @classmethod
    def get_step_definitions(cls, kind, text):
        s = ' '.join((kind, text))
        for step_definition in cls.step_definitions:
            match = step_definition.match(s)
            if match:
                yield step_definition, match
    
    @classmethod
    def get_step_definition(cls, kind, text):
        step_definitions = list(cls.get_step_definitions(kind, text))
        if len(step_definitions) == 1:
            return step_definitions[0]
        elif len(step_definitions) > 1:
            raise StepDefinitionError(
                'more than one match for %r %r: %s',
                kind, text,
                [step_definition for step_definition, match in step_definitions]
            )
        else:
            return None, None
    
    @classmethod
    def clear(cls):
        cls.step_definitions = []
    
    def match(self, s):
        return self.pattern.search(s)
    
    def __call__(self, step):
        self.definition(step, *step.match.groups())
    
    def getsourcebits(self):
        return self.pattern.pattern, inspect.getsource(self.definition)


def define_step(pattern, definition):
    StepDefinition(pattern, definition)

def step(pattern):
    def step_definition(definition):
        StepDefinition(pattern, definition)
        return definition
    return step_definition


#.............................................................................
#   feature.py
