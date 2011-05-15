# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_scenario.py --- Wishes scenario vows
#=============================================================================
import unittest

import mock
from should_dsl import should

from wishes.feature import Scenario


class ScenarioTest(unittest.TestCase):
    
    def test_gets_itself_skipped_if_without_steps(self):
        scenario = Scenario('Test scenario')
        feature = mock.Mock()
        scenario.run(feature)
        len(feature.method_calls) |should| be(1)
        feature.skipTest |should| be_called_once_with('no steps defined')

#.............................................................................
#   test_scenario.py
