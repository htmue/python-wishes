# -*- coding:utf-8 -*-
# Copyright 2011 Hans-Thomas Mueller
# Distributed under the terms of the GNU General Public License v2
#=============================================================================
#   autorunner.py --- Run tests automatically
#=============================================================================
import logging
import os
import re
import subprocess
import threading

from db import Database
from observer.tree import TreeObserver


log = logging.getLogger(__name__)

DEFAULT_FILEPATTERN = re.compile(r'.*\.(py|txt|yaml|sql|html|js|css|feature)$')

class AutocheckObserver(TreeObserver):
    
    def __init__(self, dir, args, filepattern=DEFAULT_FILEPATTERN, database=None):
        self._lock = threading.Lock()
        self.child = None
        self.args = args + ['--single']
        for arg in args:
            if arg.startswith('--python='):
                self.args = [arg.split('=', 1)[1]] + self.args
        self.db = database
        super(AutocheckObserver, self).__init__(dir, filepattern, ignored_dirs_pattern(dir))
    
    @property
    def child(self):
        with self._lock:
            return self._child
    
    @child.setter
    def child(self, child):
        with self._lock:
            self._child = child
    
    def kill_child(self):
        child = self.child
        if child is not None:
            # child.terminate()
            # child.send_signal(signal.SIGINT)
            return True
    
    def run_tests(self, args):
        self.child = subprocess.Popen(args, close_fds=True)
        self.child.wait()
        returncode = self.child.returncode
        self.child = None
        return returncode
    
    def run_vows(self):
        returncode = self.run_tests(self.args)
        if self.db is None:
            return False
        try:
            return self.db.run_again()
        finally:
            self.db.close()
    
    def action(self, entries):
        while self.run_vows():
            pass


def ignored_dirs_pattern(dir):
    dirs = list(ignored_dirs(dir))
    if dirs:
        pattern = r'(%s)$' % '|'.join(dirs)
        log.debug('ignored_dirs_pattern: %s', pattern)
        return re.compile(pattern)

def ignored_dirs(dir):
    git_exclude = os.path.join(dir, '.git', 'info', 'exclude')
    git_ignore = os.path.join(dir, '.gitignore')
    for name in (git_exclude, git_ignore):
        for ignore in ignored_dirs_from_file(dir, name):
            log.debug('ignored_dirs:%s:%s', name, ignore)
            yield ignore

def ignored_dirs_from_file(dir, name):
    dir_re = re.compile(r'/([^/]+)/?$')
    if os.path.exists(name):
        for line in open(name):
            match = dir_re.match(line.strip())
            if match:
                ignore = os.path.join(dir, match.group(1))
                if os.path.isdir(ignore):
                    yield ignore

#.............................................................................
#   autorunner.py
