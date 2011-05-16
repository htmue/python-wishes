# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-15.
#=============================================================================
#   test_matchers.py --- 
#=============================================================================
import unittest

import mock
from should_dsl import should, should_not

from vows import EachEqual


class EachEqualTest(unittest.TestCase):
    
    def test_sees_equality(self):
        matcher = EachEqual()(range(10))
        diff = list(matcher.differ(range(10)))
        diff |should| be_equal_to([])

    def test_gets_the_differences(self):
        left = [1, 2, 3, 4]
        right = [3, 2, 1, 4]
        matcher = EachEqual()(right)
        diff = list(matcher.differ(left))
        diff |should| be_equal_to([
            (1, 1, 3),
            (3, 3, 1),
        ])

    def test_gets_the_differences_with_different_len(self):
        left = [1, 2, 3]
        right = [3, 2, 1, 4]
        matcher = EachEqual()(right)
        diff = list(matcher.differ(left))
        diff |should| be_equal_to([
            (1, 1, 3),
            (3, 3, 1),
            (4, None, 4),
        ])



class AssertCalledOnceWithTest(unittest.TestCase):
    
    def test_asserts_called_once(self):
        obj = mock.Mock()
        obj.method('hi')
        obj.method |should| be_called_once_with('hi')

    def test_does_not_assert_when_called_twice(self):
        obj = mock.Mock()
        obj.method('hi')
        obj.method('hi')
        obj.method |should_not| be_called_once_with('hi')

    def test_does_not_assert_when_called_differently(self):
        obj = mock.Mock()
        obj.method('hit')
        obj.method |should_not| be_called_once_with('hi')


#.............................................................................
#   test_matchers.py