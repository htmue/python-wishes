# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-28.
#=============================================================================
#   db.py --- Tests database
#=============================================================================
import datetime
import os
import sqlite3
from contextlib import contextmanager

from status import Status, ok


class DatabaseError(Exception):
    pass

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
            result VARCHAR
        )''',
    )
    
    def __init__(self, path=None, basedir=None, name='.tests.db'):
        if path is None:
            basedir = os.getcwd() if basedir is None else basedir
            self.path = os.path.join(basedir, name)
        else:
            self.path = path
        self.connection = None
    
    def connect(self):
        self.connection = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.connection.row_factory = sqlite3.Row
    
    def _setup(self):
        with self.transaction() as cursor:
            cursor.execute('PRAGMA foreign_keys = ON')
            for name in self._TABLES:
                self._create_table(cursor, name)
    
    def _create_table(self, cursor, name):
        cursor.execute('CREATE TABLE IF NOT EXISTS %s' % self._TABLES[name])
    
    def close(self):
        self.connection.close()
        self.connection = None
    
    @property
    def is_connected(self):
        return self.connection is not None
    
    def ensure_connection(self):
        if not self.is_connected:
            self.connect()
            self._setup()
    
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
    
    def add_run(self):
        with self.transaction() as cursor:
            cursor.execute('INSERT INTO run(started) VALUES (?)', [datetime.datetime.utcnow()])
            self.current_run_id = cursor.lastrowid
    
    @property
    def total_runs(self):
        with self.transaction() as cursor:
            cursor.execute('SELECT count(*) FROM run')
            count = cursor.fetchone()[0]
        return count
    
    def get_run(self, run_id=None):
        with self.transaction() as cursor:
            row = self._get_run(cursor)
        return row
    
    def _get_run(self, cursor, run_id=None):
        cursor.execute('SELECT * FROM run WHERE id = ?', [run_id or self.current_run_id])
        return cursor.fetchone()
    
    def add_result(self, name, started, finished, result):
        with self.transaction() as cursor:
            result_row = self._get_result(cursor, name)
            if result_row is None:
                self._insert_result(cursor, name, started, finished, result)
            else:
                self._update_result(cursor, result_row, started, finished, result)
    
    def _insert_result(self, cursor, name, started, finished, result):
        cursor.execute('INSERT INTO result(last_run_id,name,runs,started,finished,average_time,result) VALUES (?,?,?,?,?,?,?)',
            (self.current_run_id, name, 1, started, finished, finished - started, result))
    
    def _update_result(self, cursor, result_row, started, finished, result):
        name = result_row['name']
        runs = result_row['runs'] + 1
        average_time = result_row['average_time']
        if result == ok.key:
            total_time = average_time * (runs - 1) + (finished - started)
            average_time = total_time / runs
        cursor.execute('UPDATE result SET last_run_id=?,runs=?,started=?,finished=?,average_time=?,result=? WHERE name=?',
            (self.current_run_id, runs, started, finished, average_time, result, name))
    
    def _get_result(self, cursor, name):
        cursor.execute('SELECT * FROM result WHERE name = ?', [name])
        return cursor.fetchone()
    
    def get_result(self, name):
        with self.transaction() as cursor:
            row = self._get_result(cursor, name)
        if row is None:
            raise DatabaseError('no such test case: %r' % name)
        return row
    
    def total_runs_by_test_name(self, name):
        return self.get_result(name)['runs']
    
    def _get_result_count(self, cursor, run_id, result=None):
        if result is None:
            cursor.execute('SELECT count(*) FROM result WHERE last_run_id=?', [run_id])
        else:
            cursor.execute('SELECT count(*) FROM result WHERE result=? AND last_run_id=?', (result, run_id))
        return cursor.fetchone()[0]
    
    def _get_result_counts(self, cursor, run_id):
        for status in Status.ordered:
            if status.name != ok.name:
                yield status.name_plural, self._get_result_count(cursor, run_id, status.key)
    
    def finish_run(self, full):
        with self.transaction() as cursor:
            run_id = self.current_run_id
            data = dict(self._get_result_counts(cursor, run_id))
            data.update(
                run_id = run_id,
                finished = datetime.datetime.utcnow(),
                wasSuccessful = data['errors'] == data['failures'] == 0,
                testsRun = self._get_result_count(cursor, run_id),
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
            run = self._get_run(cursor, run_id)
            if full and run['wasSuccessful']:
                self._clean_history(cursor)
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
    
    def collect_results_after(self, run_id, result=ok.key, exclude=True):
        with self.transaction() as cursor:
            cursor.execute('''SELECT name FROM result WHERE last_run_id IN (
                SELECT id FROM run WHERE started>(
                    SELECT started FROM run WHERE id=?
                )) AND result%s?''' % ('=', '!=')[bool(exclude)], (run_id, result))
            for row in cursor.fetchall():
                yield row[0]
    
    def clean_history(self):
        with self.transaction() as cursor:
            self._clean_history(cursor)
    
    def _clean_history(self, cursor):
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
