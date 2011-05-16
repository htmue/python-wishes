# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   loader.py --- Feature loader
#=============================================================================
import re
import unicodedata
import unittest

from feature import FeatureTest, Scenario
from parser import Parser, LogHandler


class Handler(LogHandler):
    
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
    
    def finish_parse(self):
        self.Feature = None
    
    def start_feature(self, title):
        class Feature(FeatureTest, self.TestCase):
            pass
        Feature.__name__ = self.make_feature_name(title)
        self.Feature = Feature
        self.background = None
    
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
    
    def start_step(self, kind, statement):
        self.scenario.add_step(kind, statement)
    
    def make_feature_name(self, title):
        return 'Feature_' + slugify(title)
    
    def make_scenario_method_name(self, title):
        return 'test_Scenario_' + slugify(title)

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
