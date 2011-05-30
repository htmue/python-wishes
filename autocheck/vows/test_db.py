# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-28.
#=============================================================================
#   test_db.py --- Tests database vows
#=============================================================================
import datetime
from functools import partial

from should_dsl import should, should_not

from autocheck.compat import unittest
from autocheck.db import Database, timedelta_to_float, RunDoesNotExist, ResultDoesNotExist
from autocheck.status import ok, error, fail, skip


class DatabaseVows(unittest.TestCase):
    
    def setUp(self):
        self.db = Database(path=':memory:')
    
    def test_can_connect_to_database(self):
        self.db.connect()
        
        self.db |should| be_connected
    
    def test_can_close_database(self):
        self.db.connect()
        
        self.db.close()
        
        self.db |should_not| be_connected
    
    def test_can_add_test_run(self):
        self.db.add_run()
        
        self.db.current_run_id |should| be(1)
        self.db.total_runs |should| be(1)
    
    def test_can_count_test_runs(self):
        for i in range(5):
            self.db.add_run()
            
            self.db.current_run_id |should| be(i + 1)
            self.db.total_runs |should| be(i + 1)
    
    def test_can_load_test_run_object(self):
        before = datetime.datetime.utcnow()
        self.db.add_run()
        after = datetime.datetime.utcnow()
        
        run = self.db.get_run()
        
        run['id'] |should| be(1)
        run['started'] |should| be_greater_than(before)
        run['started'] |should| be_less_than(after)
    
    def test_raises_RunDoesNotExist_when_no_run_exists(self):
        self.db.get_run |should| throw(RunDoesNotExist)
    
    def test_raises_RunDoesNotExist_when_run_does_not_exist(self):
        get_run = partial(self.db.get_run, 1)
        
        get_run |should| throw(RunDoesNotExist)
    
    def add_result(self, name, status=ok.key, started=None, finished=None, run=None):
        if run is None:
            self.db.add_run()
            run = self.db.get_run()
        if finished is None:
            finished = datetime.datetime.utcnow()
        if started is None:
            started = run['started']
        self.db.add_result(name, started, finished, status)
    
    def test_can_add_result(self):
        name = 'test_name (that.SpecialTest)'
        
        self.add_result(name)
        
        self.db.total_runs_by_test_name(name) |should| be(1)
    
    def test_raises_ResultDoesNotExist_when_test_does_not_exist(self):
        get_result = partial(self.db.get_last_result, 'hi')
        
        get_result |should| throw(ResultDoesNotExist)
    
    def test_knows_number_of_test_runs(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        self.add_result(name)
        
        self.db.total_runs_by_test_name(name) |should| be(2)
    
    def test_knows_average_test_runtime(self):
        name = 'test_name (that.SpecialTest)'
        now = datetime.datetime.utcnow()
        started = now
        finished = started + datetime.timedelta(seconds=1)
        self.add_result(name, started=started, finished=finished)
        started = finished
        finished = started + datetime.timedelta(seconds=2)
        self.add_result(name, started=started, finished=finished)
        
        test = self.db.get_test(name)
        
        average_time = timedelta_to_float(test['average_time'])
        average_time |should| close_to(1.5, delta=.1)
    
    def test_knows_last_run_of_test_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        self.add_result(name)
        
        result = self.db.get_last_result(name)
        
        result['run_id'] |should| be_equal_to(self.db.current_run_id)
    
    def test_can_finish_test_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        
        run = self.db.finish_run(True)
        
        run['testsRun'] |should| be(1)
        run['wasSuccessful'] |should| be(True)
        run['errors'] |should| be(0)
        run['failures'] |should| be(0)
        run['skipped'] |should| be(0)
        run['expectedFailures'] |should| be(0)
        run['unexpectedSuccesses'] |should| be(0)
    
    def test_knows_id_of_last_successful_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, status=ok.key)
        self.db.finish_run(False)
        self.add_result(name, status=fail.key)
        self.db.finish_run(False)
        
        self.db.get_last_successful_run_id() |should| be(1)
    
    def test_handles_last_successful_run_id_edge_case_empty(self):
        self.db.get_last_successful_run_id() |should| be(None)
    
    def test_handles_last_successful_run_id_edge_case_only_failures(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, status=fail.key)
        self.db.finish_run(True)
        
        self.db.get_last_successful_run_id() |should| be(None)
    
    def test_cleans_history_when_finishing_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        self.db.finish_run(False)
        self.add_result(name)
        self.db.finish_run(True)
        self.add_result(name)
        self.db.finish_run(False)
        
        self.db.total_runs |should| be(2)
    
    def test_does_not_clean_history_after_unsuccessful_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, status=ok.key)
        self.db.finish_run(True)
        self.add_result(name, status=fail.key)
        self.db.finish_run(True)
        
        self.db.total_runs |should| be(2)
    
    def test_does_not_clean_history_after_partial_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, status=ok.key)
        self.db.finish_run(True)
        self.add_result(name, status=ok.key)
        self.db.finish_run(False)
        
        self.db.total_runs |should| be(2)
    
    def test_keeps_track_of_full_test_runs(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        run = self.db.finish_run(True)
        
        run['full'] |should| be(True)
    
    def test_keeps_track_of_partial_test_runs(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        run = self.db.finish_run(False)
        
        run['full'] |should| be(False)
    
    def test_knows_id_of_last_run(self):
        for d in range(3):
            name = 'test_name_%d (that.SpecialTest)' % d
            self.add_result(name)
            run = self.db.finish_run(True)
        
        self.db.get_last_run_id() |should| be_equal_to(run['id'])
    
    def test_knows_id_of_last_successful_full_run(self):
        name = 'test_name_%d (that.SpecialTest)'
        self.add_result(name % 1, status=ok.key)
        run_1 = self.db.finish_run(True)
        self.add_result(name % 2, status=ok.key)
        run_2 = self.db.finish_run(False)
        self.add_result(name % 3, status=fail.key)
        run_3 = self.db.finish_run(True)
        
        self.db.get_last_successful_full_run_id() |should| be_equal_to(run_1['id'])
    
    def test_can_collect_non_successful_tests_after_certain_run(self):
        name = 'test_name_%d_%s (that.SpecialTest)'
        run_ids = []
        for i, status in enumerate((ok, fail, error, ok, skip)):
            self.add_result(name % (i, status.name), status=status.key)
            run_ids.append(self.db.finish_run(False)['id'])
        
        results = list(self.db.collect_results_after(run_ids[0]))
        results |should| each_be_equal_to([
            'test_name_1_FAIL (that.SpecialTest)',
            'test_name_2_ERROR (that.SpecialTest)',
            'test_name_4_skipped (that.SpecialTest)',
        ])
        
        results = list(self.db.collect_results_after(run_ids[2]))
        results |should| each_be_equal_to([
            'test_name_4_skipped (that.SpecialTest)',
        ])
        
        results = list(self.db.collect_results_after(run_ids[4]))
        results |should| be_empty
    
    def test_can_collect_non_successful_tests_after_certain_run_that_have_been_successful_later(self):
        name = 'test_name (that.SpecialTest)'
        run_ids = []
        for status in (ok, fail, error, ok, skip):
            self.add_result(name, status=status.key)
            run_ids.append(self.db.finish_run(False)['id'])
        
        results = list(self.db.collect_results_after(run_ids[0]))
        results |should| each_be_equal_to([
            'test_name (that.SpecialTest)',
        ])
        
        results = list(self.db.collect_results_after(run_ids[2]))
        results |should| each_be_equal_to([
            'test_name (that.SpecialTest)',
        ])
        
        results = list(self.db.collect_results_after(run_ids[4]))
        results |should| be_empty

#.............................................................................
#   test_db.py
