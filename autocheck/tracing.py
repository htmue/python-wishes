# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   tracing.py --- Debug tracing support
#=============================================================================
import functools
import logging
import types


trace = logging.getLogger(__name__)


def tracing(f, name, log=trace.debug):
    @functools.wraps(f)
    def traced_f(*args, **kwargs):
        log('[%#x]%s(%s,%s)', id(args[0]), name, args[1:], kwargs)
        result = f(*args, **kwargs)
        log('[%#x]%s(%s,%s) => %r', id(args[0]), name, args[1:], kwargs, result)
        return result
    return traced_f

class MetaLogger(type):

    def __new__(self, classname, bases, classdict):
        classdict.setdefault('log', logging.getLogger('%s.%s' % (classdict['__module__'], classname)))
        return type.__new__(self, classname, bases, classdict)

class MetaTracer(type):

    def __new__(self, classname, bases, classdict):
        classdict.setdefault('log', logging.getLogger('%s.%s' % (classdict['__module__'], classname)))
        if trace.isEnabledFor(logging.DEBUG):
            for f in classdict:
                m = classdict[f]
                if isinstance(m, types.FunctionType):
                    classdict[f] = tracing(m, '%s.%s' % (classname, f), log=classdict['log'].debug)
        return type.__new__(self, classname, bases, classdict)

class Logger(object):
    __metaclass__ = MetaLogger

class Tracer(object):
    __metaclass__ = MetaTracer

def setLevel(level):
    trace.setLevel(level)

#.............................................................................
#   tracing.py