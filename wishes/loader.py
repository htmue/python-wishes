# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   loader.py --- Feature loader
#=============================================================================
import re
import unicodedata
import unittest

from feature import FeatureTest, Scenario, Hashes
from parser import Parser


class Handler(object):
    
    def __init__(self, test_case_class=None, scenario_class=None):
        if test_case_class is None:
            self.TestCase = unittest.TestCase
        elif not issubclass(test_case_class, unittest.TestCase):
            raise ValueError('%r is not subclass of unittest.TestCase' % test_case_class)
        else:
            self.TestCase = test_case_class
        if scenario_class is None:
            self.Scenario = Scenario
        elif not issubclass(scenario_class, Scenario):
            raise ValueError('%r is not subclass of Scenario' % scenario_class)
        else:
            self.Scenario = scenario_class
    
    def start_parse(self, name):
        self.feature_name = name
        self.suite = None
        self.lines = None
    
    def finish_parse(self):
        self.Feature = None
    
    def start_feature(self, title):
        class Feature(FeatureTest, self.TestCase):
            pass
        Feature.__name__ = self.make_feature_name(title)
        self.Feature = Feature
        self.background = None
        self.multilines = None
        self.hashes = None
    
    def finish_feature(self):
        self.suite = unittest.defaultTestLoader.loadTestsFromTestCase(self.Feature)
    
    def start_scenario(self, title):
        self.scenario_method = self.make_scenario_method_name(title)
        self.scenario = self.Scenario(title, self.background)
    
    def finish_scenario(self):
        self.Feature.add_scenario(self.scenario_method, self.scenario)
    
    def start_background(self, title):
        self.scenario = self.Scenario(title)
    
    def finish_background(self):
        self.background = self.scenario
    
    def start_outline(self, title):
        self.scenario = self.Scenario(title, background=self.background)
    
    def finish_outline(self):
        self.outline = self.scenario
    
    def start_examples(self, title):
        self.examples = self.make_example_name(title)
    
    def finish_examples(self):
        self.hashes.fix_keys_for_outline()
        for n, example in enumerate(self.hashes):
            scenario = self.Scenario(outline=(self.outline, example))
            title = '%s %d %s' % (scenario.title, n + 1, self.examples)
            scenario_method = self.make_scenario_method_name(title)
            self.Feature.add_scenario(scenario_method, scenario)
        self.hashes = None
    
    def start_step(self, kind, statement):
        self.step = kind, statement
    
    def finish_step(self):
        if self.multilines is not None:
            self.scenario.add_step(*self.step, multilines=self.multilines)
            self.multilines = None
        elif self.hashes is not None:
            self.scenario.add_step(*self.step, hashes=self.hashes)
            self.hashes = None
        else:
            self.scenario.add_step(*self.step)
    
    def start_multiline(self, indent):
        self.lines = []
    
    def finish_multiline(self):
        self.multilines = self.lines
        self.lines = None
    
    def start_hash(self, *keys):
        self.hashes = Hashes(keys)
    
    def hash_data(self, *values):
        self.hashes.add_row(values)
    
    def finish_hash(self):
        pass
    
    def data(self, data):
        if self.lines is not None:
            self.lines.append(data)
    
    def make_feature_name(self, title):
        return 'Feature_' + slugify(title)
    
    def make_scenario_method_name(self, title):
        return 'test_Scenario_' + slugify(title)
    
    def make_example_name(self, title):
        return 'Example_' + slugify(title)

def slugify(value):
    value = unicodedata.normalize('NFKD', value.decode('utf-8')).encode('ascii', 'ignore')
    value = re.sub('[^\w\s-]', '', value).strip()
    return re.sub('[-\s]+', '_', value)


class Loader(object):
    
    def load_feature(self, feature, test_case_class=None, scenario_class=None):
        handler = Handler(test_case_class, scenario_class)
        parser = Parser(handler)
        parser.parse(feature.strip())
        return handler.suite

defaultLoader = Loader()
load_feature = defaultLoader.load_feature

#.............................................................................
#   loader.py
