# -*- coding:utf-8 -*-
# Copyright 2011 Hans-Thomas Mueller
# Distributed under the terms of the GNU General Public License v2
#=============================================================================
#   main.py --- Run tests automatically
#=============================================================================
import logging
import os
import signal
import sys

from nose.core import TestProgram

from runner import AutocheckObserver


log = logging.getLogger('autocheck')


class Unbuffered:

    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

def handle_term():
    def sighandler(signum, frame):
        os.kill(os.getpid(), signal.SIGINT)
    signal.signal(signal.SIGTERM, sighandler)

def single(args):
    sys.stdout=Unbuffered(sys.stdout)
    if '--wishes' in args:
        raise NotImplementedError('wishes runner')
    else:
        TestProgram(argv=args)

def autocheck(args):
    handle_term()
    root = AutocheckObserver('.', args)
    log.debug('starting autocheck observer')
    try:
        root.loop()
    except KeyboardInterrupt:
        print 'Got signal, exiting.'
        root.kill_child()

def main(args=sys.argv):
    if '--single' in args:
        args.remove('--single')
        single(args)
    else:
        if args[0].startswith( __file__):
            args = [os.path.abspath(sys.executable), '-m', 'autocheck.main'] + args[1:]
        autocheck(args)

if __name__ == '__main__':
    main()

#.............................................................................
#   main.py
