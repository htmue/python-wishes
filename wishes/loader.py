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

    def start_parse(self, name):
        self.feature_name = name
        self.suite = None

    def finish_parse(self):
        self.Feature = None

    def start_feature(self, title):
        class Feature(FeatureTest):
            pass
        Feature.__name__ = 'Feature_' + slugify(title)
        self.Feature = Feature
        self.scenarios = []

    def finish_feature(self):
        self.Feature.scenarios = dict(self.scenarios)
        self.suite = unittest.defaultTestLoader.loadTestsFromTestCase(self.Feature)

    def start_scenario(self, title):
        self.scenario_method = 'test_Scenario_' + slugify(title)
        self.scenario = Scenario(title)

    def finish_scenario(self):
        self.scenarios.append((self.scenario_method, self.scenario))
        setattr(self.Feature, self.scenario_method, self.Feature.runTest)


def slugify(value):
    value = unicodedata.normalize('NFKD', value.decode('utf-8')).encode('ascii', 'ignore')
    value = re.sub('[^\w\s-]', '', value).strip()
    return re.sub('[-\s]+', '_', value)


class Loader(object):
    
    def load_feature(self, feature):
        handler = Handler()
        parser = Parser(handler)
        parser.parse(feature.strip())
        return handler.suite

defaultLoader = Loader()
load_feature = defaultLoader.load_feature

#.............................................................................
#   loader.py
