# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-28.
#=============================================================================
#   db.py --- Tests database
#=============================================================================
import datetime
import functools
import os
import sqlite3
from contextlib import contextmanager

from status import Status, ok


class DatabaseError(Exception): pass
class DoesNotExist(DatabaseError): pass
class RunDoesNotExist(DoesNotExist): pass
class ResultDoesNotExist(DoesNotExist): pass

class Database(object):
    _TABLES = dict(
    
        run = '''run(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started TIMESTAMP,
            finished TIMESTAMP,
            wasSuccessful BOOLEAN,
            testsRun INTEGER,
            full BOOLEAN,
            errors INTEGER,
            failures INTEGER,
            skipped INTEGER,
            expectedFailures INTEGER,
            unexpectedSuccesses INTEGER
            )''',
    
        result = '''result(
            name VARCHAR PRIMARY KEY,
            runs INTEGER,
            started TIMESTAMP,
            finished TIMESTAMP,
            average_time TIMEDELTA,
            last_run_id INTEGER REFERENCES run(id),
            status VARCHAR
        )''',
    )
    
    def __init__(self, path=None, basedir=None, name='.tests.db'):
        if path is None:
            basedir = os.getcwd() if basedir is None else basedir
            self.path = os.path.join(basedir, name)
        else:
            self.path = path
        self.connection = None
        self.current_run_id = None
    
    def connect(self):
        self.connection = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.connection.row_factory = sqlite3.Row
    
    def close(self):
        self.connection.close()
        self.connection = None
    
    @property
    def is_connected(self):
        return self.connection is not None
    
    def ensure_connection(self):
        if not self.is_connected:
            self.connect()
            self.setup()
    
    @contextmanager
    def transaction(self):
        self.ensure_connection()
        try:
            yield self.connection.cursor()
        except:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()
    
    def with_cursor(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            cursor = kwargs.pop('cursor', None)
            if cursor is None:
                with self.transaction() as cursor:
                    return method(self, cursor, *args, **kwargs)
            else:
                return method(self, cursor, *args, **kwargs)
        return wrapper
    
    @with_cursor
    def setup(self, cursor):
        cursor.execute('PRAGMA foreign_keys = ON')
        for name in self._TABLES:
            self.create_table(name, cursor=cursor)
    
    @with_cursor
    def create_table(self, cursor, name):
        cursor.execute('CREATE TABLE IF NOT EXISTS %s' % self._TABLES[name])
    
    @with_cursor
    def add_run(self, cursor):
        cursor.execute('INSERT INTO run(started) VALUES (?)', [datetime.datetime.utcnow()])
        self.current_run_id = cursor.lastrowid
    
    @property
    def total_runs(self):
        with self.transaction() as cursor:
            cursor.execute('SELECT count(*) FROM run')
            count = cursor.fetchone()[0]
        return count
    
    @with_cursor
    def get_run(self, cursor, run_id=None):
        if run_id is None:
            run_id = self.current_run_id
        if run_id is None:
            raise RunDoesNotExist()
        cursor.execute('SELECT * FROM run WHERE id = ?', [run_id])
        run = cursor.fetchone()
        if run is None:
            raise RunDoesNotExist(run_id)
        return run
    
    @with_cursor
    def add_result(self, cursor, name, started, finished, status):
        try:
            result = self.get_result(name, cursor=cursor)
        except ResultDoesNotExist:
            self._insert_result(cursor, name, started, finished, status)
        else:
            self._update_result(cursor, result, started, finished, status)
    
    def _insert_result(self, cursor, name, started, finished, status):
        cursor.execute('INSERT INTO result(last_run_id,name,runs,started,finished,average_time,status) VALUES (?,?,?,?,?,?,?)',
            (self.current_run_id, name, 1, started, finished, finished - started, status))
    
    def _update_result(self, cursor, result, started, finished, status):
        name = result['name']
        runs = result['runs'] + 1
        average_time = result['average_time']
        if status == ok.key:
            total_time = average_time * (runs - 1) + (finished - started)
            average_time = total_time / runs
        cursor.execute('UPDATE result SET last_run_id=?,runs=?,started=?,finished=?,average_time=?,status=? WHERE name=?',
            (self.current_run_id, runs, started, finished, average_time, status, name))
    
    @with_cursor
    def get_result(self, cursor, name):
        cursor.execute('SELECT * FROM result WHERE name = ?', [name])
        row = cursor.fetchone()
        if row is None:
            raise ResultDoesNotExist(name)
        return row
    
    def total_runs_by_test_name(self, name):
        return self.get_result(name)['runs']
    
    @with_cursor
    def get_result_count(self, cursor, run_id, status=None):
        if status is None:
            cursor.execute('SELECT count(*) FROM result WHERE last_run_id=?', [run_id])
        else:
            cursor.execute('SELECT count(*) FROM result WHERE status=? AND last_run_id=?', (status, run_id))
        return cursor.fetchone()[0]
    
    @with_cursor
    def get_result_counts(self, cursor, run_id):
        for status in Status.ordered:
            if status.name != ok.name:
                yield status.name_plural, self.get_result_count(run_id, status.key, cursor=cursor)
    
    def finish_run(self, full):
        with self.transaction() as cursor:
            run_id = self.current_run_id
            data = dict(self.get_result_counts(run_id, cursor=cursor))
            data.update(
                run_id = run_id,
                finished = datetime.datetime.utcnow(),
                wasSuccessful = data['errors'] == data['failures'] == 0,
                testsRun = self.get_result_count(run_id, cursor=cursor),
                full = full,
            )
            cursor.execute('''UPDATE run SET
                finished=:finished,
                wasSuccessful=:wasSuccessful,
                testsRun=:testsRun,
                full=:full,
                errors=:errors,
                failures=:failures,
                skipped=:skipped,
                expectedFailures=:expectedFailures,
                unexpectedSuccesses=:unexpectedSuccesses WHERE id=:run_id''', data)
            run = self.get_run(run_id, cursor=cursor)
            if full and run['wasSuccessful']:
                self.clean_history(cursor=cursor)
        return run
    
    def get_last_run_id(self, where=''):
        with self.transaction() as cursor:
            cursor.execute('SELECT id FROM run %s ORDER BY finished DESC LIMIT 1' % where)
            run_id = cursor.fetchone()
        if run_id is not None:
            return run_id[0]
    
    def get_last_successful_run_id(self):
        return self.get_last_run_id('WHERE wasSuccessful=1')
    
    def get_last_successful_full_run_id(self):
        return self.get_last_run_id('WHERE wasSuccessful=1 AND full=1')
    
    def collect_results_after(self, run_id, status=ok.key, exclude=True):
        with self.transaction() as cursor:
            cursor.execute('''SELECT name FROM result WHERE last_run_id IN (
                SELECT id FROM run WHERE started>(
                    SELECT started FROM run WHERE id=?
                )) AND status%s?''' % ('=', '!=')[bool(exclude)], (run_id, status))
            for row in cursor.fetchall():
                yield row[0]
    
    @with_cursor
    def clean_history(self, cursor):
        cursor.execute('DELETE FROM run WHERE (SELECT count(*) FROM result WHERE last_run_id=run.id)=0')


def timedelta_to_float(delta):
    if hasattr(delta, 'total_seconds'):
        return delta.total_seconds()
    else:
        return (delta.microseconds + (delta.seconds + delta.days * 24. * 3600.) * 10**6) / 10**6

def adapt_timedelta(delta):
    return str(timedelta_to_float(delta))

def convert_timedelta(s):
    return datetime.timedelta(seconds=float(s))

sqlite3.register_adapter(datetime.timedelta, adapt_timedelta)
sqlite3.register_converter('timedelta', convert_timedelta)

def convert_boolean(s):
    return bool(int(s))

sqlite3.register_converter('boolean', convert_boolean)

#.............................................................................
#   db.py
