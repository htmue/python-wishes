# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   feature.py --- Feature test case
#=============================================================================
import unittest


class FeatureTest(unittest.TestCase):
    
    def runTest(self):
        if self.scenario_method == 'runTest':
            self.skipTest('no scenarios defined')
        self.scenario.run(self)
    
    @property
    def scenario_method(self):
        return self.id().rsplit('.', 1)[1]

    @property
    def scenario(self):
        return self.scenarios[self.scenario_method]


class Scenario(object):
    
    def __init__(self, title):
        self.title = title
        self.steps = []
    
    def run(self, feature):
        if not self.steps:
            feature.skipTest('no steps defined')


#.............................................................................
#   feature.py
