# -*- coding:utf-8 -*-
# Copyright 2011 Hans-Thomas Mueller
# Distributed under the terms of the GNU General Public License v2
#=============================================================================
#   runner.py --- Run tests automatically
#=============================================================================
import json
import logging
import os
import re
import subprocess
import threading

from observer.tree import TreeObserver


log = logging.getLogger(__name__)

DEFAULT_FILEPATTERN = re.compile(r'.*\.(py|txt|yaml|sql|html|js|css|feature)$')

class AutocheckObserver(TreeObserver):
    
    def __init__(self, dir, args, filepattern=DEFAULT_FILEPATTERN):
        self._lock = threading.Lock()
        self.child = None
        self.args = args + ['--single']
        self.wishes = False
        for arg in args:
            if arg.startswith('--python='):
                self.args = [arg.split('=', 1)[1]] + self.args
            if arg == '--wishes':
                self.wishes = True
        if self.wishes:
            self.args.remove('--wishes')
        self.failed_vows = self.failed_wishes = None
        self.state = 'wishes' if self.wishes else 'all'
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
            child.terminate()
    
    def run_grep(self, args, pattern=None):
        self.log.debug('run_grep:%r:%s', pattern.pattern, args)
        self.child = subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=1)
        match = None
        while True:
            line = self.child.stdout.readline()
            if not line:
                self.child.wait()
                returncode = self.child.returncode
                self.child = None
                return match, returncode
            print line.rstrip()
            if pattern is not None:
                m = pattern.match(line)
                if m:
                    match = m
    
    def run_wishes(self):
        args = (self.args + self.failed_wishes[:1] if self.failed_wishes else self.args) + ['--wishes']
        print args
        match, returncode = self.run_grep(args, re.compile(r'FAILED FEATURES (.*)'))
        if match:
            self.failed_wishes = json.loads(match.group(1))
        else:
            self.failed_wishes = None
        return returncode == 0
    
    def run_vows(self):
        args = self.args + self.failed_vows if self.failed_vows else self.args
        match, _ = self.run_grep(args, re.compile(r'FAILED MODULES (.*)'))
        if match:
            self.failed_vows = json.loads(match.group(1))
        else:
            self.failed_vows = None
        return not match
    
    def action(self, entries):
        if self.state == 'all':
            if self.run_vows():
                if self.wishes:
                    self.state = 'wishes'
                    self.action(entries)
            else:
                self.state = 'failures'
        elif self.state == 'failures':
            if self.run_vows():
                self.state = 'all'
                self.action(entries)
        elif self.state == 'wishes':
            if not self.run_wishes():
                self.state = 'all'


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
#   runner.py
