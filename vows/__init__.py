# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   __init__.py --- Vows API promises, tests support code
#=============================================================================
import unittest
from itertools import izip_longest

from should_dsl import matcher, should


@matcher
class EachEqual(object):
    name = 'each_be_equal_to'
    
    def __call__(self, expected):
        self._expected = expected
        return self

    def differ(self, given):
        for n, (left, right) in enumerate(izip_longest(given, self._expected)):
            if left != right:
                yield n + 1, left, right

    def match(self, given):
        diff = list(self.differ(given))
        self.diff = '\n\t'.join('%d: %s is not equal to %s' % item for item in diff)
        return not diff
    
    def message_for_failed_should(self):
        return 'sequences differ\n\t' + self.diff


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


@matcher
def be_equal_to():
    return (lambda x, y: x == y, '%r is %sequal to %r')


#.............................................................................
#   __init__.py
