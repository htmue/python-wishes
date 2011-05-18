# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   __init__.py --- Vows API promises, tests support code
#=============================================================================
from itertools import izip_longest

from should_dsl import matcher


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
        self.diff = '\n\t'.join('%d: %r is not equal to %r' % item for item in diff)
        return not diff
    
    def message_for_failed_should(self):
        return 'sequences differ\n\t' + self.diff


@matcher
def be_equal_to():
    return (lambda x, y: x == y, '%r is %sequal to %r')

@matcher
def be_in():
    return (lambda item, container: item in container, '%r is %sinto %r')

@matcher
class AssertCalledOnceWith(object):
    name = 'be_called_once_with'
    
    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self
    
    def match(self, given):
        try:
            given.assert_called_once_with(*self.args, **self.kwargs)
        except AssertionError as error:
            self.error = error
            return False
        else:
            return True
    
    def message_for_failed_should(self):
        return str(self.error)

#.............................................................................
#   __init__.py
