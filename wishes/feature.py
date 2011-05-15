# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   feature.py --- Feature test case
#=============================================================================
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
    
    def __init__(self, title):
        self.title = title
        self.steps = []
    
    def run(self, feature):
        if not self.steps:
            feature.skipTest('no steps defined')


#.............................................................................
#   feature.py
