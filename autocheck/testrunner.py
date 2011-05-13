# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-12.
#=============================================================================
#   testrunner.py --- Running tests
#=============================================================================
import os
import sys
import time
from unittest import result
from unittest.signals import registerResult
from contextlib import contextmanager
import termstyle
import yaml


try:
    from growler import Notifier
except ImportError:
    growler = None
else:
    growler = Notifier()



class ColourDecorator(object):
    """Used to decorate file-like objects' 'write' method to accept colours"""
    def __init__(self, stream):
        self.stream = stream

    def __getattr__(self, attr):
        if attr in ('stream', '__getstate__'):
            raise AttributeError(attr)
        return getattr(self.stream, attr)

    def write(self, arg=None, colour=None):
        if arg:
            if colour is not None:
                arg = colour(arg)
        self.stream.write(arg)


class ColourWritelnDecorator(ColourDecorator):
    """Used to decorate file-like objects with a handy 'writeln' method"""
    def __init__(self, stream):
        self.stream = stream

    def __getattr__(self, attr):
        if attr in ('stream', '__getstate__'):
            raise AttributeError(attr)
        return getattr(self.stream, attr)

    def writeln(self, arg=None, colour=None):
        if arg:
            self.write(arg, colour=colour)
        self.write('\n') # text-mode streams translate to \r\n if needed


class ColourScheme(object):
    
    def __init__(self, scheme):
        if isinstance(scheme, basestring):
            filename = os.path.join(os.path.dirname(__file__), 'colourschemes', scheme + '.yaml')
            self.scheme = yaml.load(open(filename))
        else:
            self.scheme = scheme

    def __getattr__(self, key):
        if self.scheme is not None:
            colour = self.scheme.get(key)
            if isinstance(colour, basestring):
                return getattr(termstyle, colour)
            elif colour is None:
                return lambda x: x
            else:
                return compose(getattr(termstyle, c) for c in colour)

def compose(iterable):
    def compose(arg):
        for f in iterable:
            arg = f(arg)
        return arg
    return compose


class TestResult(result.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by TestRunner.
    """
    separator1 = '=' * 70
    separator2 = '-' * 70

    def __init__(self, stream=sys.stderr, descriptions=True, verbosity=1, colourscheme='light'):
        super(TestResult, self).__init__()
        self.scheme = colourscheme if isinstance(colourscheme, ColourScheme) else ColourScheme(colourscheme)
        self.stream = stream if isinstance(stream, ColourWritelnDecorator) else ColourWritelnDecorator(stream)
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.descriptions = descriptions
        self.success_count = 0

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return '\n'.join((str(test), doc_first_line))
        else:
            return str(test)
    
    def _write(self, all, dots, colour):
        if self.showAll and all is not None:
            self.stream.writeln(all, colour=colour)
        elif self.dots and dots is not None:
            self.stream.write(dots, colour=colour)
            self.stream.flush()

    def startTest(self, test):
        super(TestResult, self).startTest(test)
        if self.showAll:
            self.stream.write(self.getDescription(test))
            self.stream.write(' ... ')
            self.stream.flush()

    def addSuccess(self, test):
        super(TestResult, self).addSuccess(test)
        self.success_count += 1
        self._write('ok', '.', colour=self.scheme.ok)

    def addError(self, test, err):
        super(TestResult, self).addError(test, err)
        self._write('ERROR', 'E', colour=self.scheme.error)

    def addFailure(self, test, err):
        super(TestResult, self).addFailure(test, err)
        self._write('FAIL', 'F', colour=self.scheme.fail)

    def addSkip(self, test, reason):
        super(TestResult, self).addSkip(test, reason)
        colour = self.scheme.skip
        if self.showAll:
            self._write('skipped {0!r}'.format(reason), None, colour=colour)
        elif self.dots:
            self._write(None, 's', colour=colour)

    def addExpectedFailure(self, test, err):
        super(TestResult, self).addExpectedFailure(test, err)
        self._write('expected failure', 'x', colour=self.scheme.expected_failure)

    def addUnexpectedSuccess(self, test):
        super(TestResult, self).addUnexpectedSuccess(test)
        self._write('unexpected success', 'u', colour=self.scheme.unexpected_success)

    def printErrors(self):
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList('ERROR', self.errors, colour=self.scheme.error)
        self.printErrorList('FAIL', self.failures, colour=self.scheme.fail)

    def printErrorList(self, flavour, errors, colour):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln('%s: %s' % (flavour, self.getDescription(test)), colour=colour)
            self.stream.writeln(self.separator2)
            self.stream.writeln('%s' % err, colour=colour)



class TestRunner(object):
    """A test runner class that displays results in textual form.

    It prints out the names of tests as they are run, errors as they
    occur, and a summary of the results at the end of the test run.
    """
    resultclass = TestResult

    def __init__(self, stream=sys.stderr, descriptions=True, verbosity=1,
                 failfast=False, buffer=False, resultclass=None,
                 colourscheme='light', growler=growler):
        self.stream = ColourWritelnDecorator(stream)
        self.scheme = ColourScheme(colourscheme)
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.growler = growler
        if resultclass is not None:
            self.resultclass = resultclass

    def _makeResult(self):
        return self.resultclass(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        startTime = time.time()
        startTestRun = getattr(result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
        try:
            test(result)
        finally:
            stopTestRun = getattr(result, 'stopTestRun', None)
            if stopTestRun is not None:
                stopTestRun()
        stopTime = time.time()
        timeTaken = stopTime - startTime
        result.printErrors()
        if hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln('Ran %d test%s in %.3fs' %
                            (run, run != 1 and 's' or '', timeTaken))
        self.stream.writeln()

        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        infos = []
        if not result.wasSuccessful():
            self.stream.write('FAILED', colour=self.scheme.FAIL)
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                infos.append((self.scheme.FAIL, 'failures: %d' % failed))
            if errored:
                infos.append((self.scheme.ERROR, 'errors: %d' % errored))
        else:
            failed = errored = None
            self.stream.write('OK', colour=self.scheme.OK)
        if skipped:
            infos.append((self.scheme.SKIP, 'skipped: %d' % skipped))
        if expectedFails:
            infos.append((
                self.scheme.EXPECTED_FAILURE,
                'expected failures: %d' % expectedFails))
        if unexpectedSuccesses:
            infos.append((
                self.scheme.UNEXPECTED_SUCCESS,
                'unexpected successes: %d' % unexpectedSuccesses))
        try:
            success = result.success_count
        except AttributeError:
            pass
        else:
            if not result.wasSuccessful():
                infos.append((self.scheme.OK, 'passed: %d' % success))
        if self.growler is not None:
            if errored:
                kind = 'error'
            elif failed:
                kind = 'fail'
            elif skipped or expectedFails:
                kind = 'pending'
            else:
                assert result.wasSuccessful()
                kind = 'pass'
            description = ['%d tests run' % run]
            if infos:
                description.append('(%s)' % ', '.join(info for _, info in infos))
            self.growler.notify(kind.title(), '\n'.join(description), dict(error='fail').get(kind, kind))
        if infos:
            self.stream.writeln(' (%s)' % (', '.join(c(info) for c, info in infos),))
        else:
            self.stream.writeln()
        return result



if __name__ == '__main__':
    import sys
    if sys.argv[0].endswith('__main__.py'):
        sys.argv[0] = 'python -m autocheck.testrunner'

    from unittest.main import main, TestProgram, USAGE_AS_MAIN
    TestProgram.USAGE = USAGE_AS_MAIN

    main(module=None, testRunner=TestRunner)


__test__ = False

#.............................................................................
#   testrunner.py

# Derived from Python-2.7.1 unittest.runner, unittest.result, traceback
# Copyright © 2001-2010 Python Software Foundation; All Rights Reserved
# http://docs.python.org/license.html
