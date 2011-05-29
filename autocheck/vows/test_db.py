# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-28.
#=============================================================================
#   test_db.py --- Tests database vows
#=============================================================================
import datetime

from should_dsl import should, should_not

from autocheck.db import Database, timedelta_to_float
from wishes.compat import unittest


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
        run = self.db.get_run()
        run['id'] |should| be(1)
        after = datetime.datetime.utcnow()
        run['started'] |should| be_greater_than(before)
        run['started'] |should| be_less_than(after)
    
    def add_result(self, name, result='.', started=None, finished=None, run=None):
        if run is None:
            self.db.add_run()
            run = self.db.get_run()
        if finished is None:
            finished = datetime.datetime.utcnow()
        if started is None:
            started = run['started']
        self.db.add_result(name, started, finished, result)
    
    def test_can_add_result(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        self.db.total_runs_by_test_name(name) |should| be(1)
    
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
        result = self.db.get_result(name)
        average_time = timedelta_to_float(result['average_time'])
        average_time |should| close_to(1.5, delta=.1)
    
    def test_knows_last_run_of_test_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        self.add_result(name)
        result = self.db.get_result(name)
        result['last_run_id'] |should| equal_to(self.db.current_run_id)
    
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
        self.db.add_run()
        run = self.db.get_run()
        # prevent finish_run from cleaning history
        self.add_result('test_other_name (that.SpecialTest)', run=run)
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, result='.', run=run)
        self.db.finish_run(True)
        self.add_result(name, result='F')
        self.db.finish_run(True)
        self.db.get_last_successful_run_id() |should| be(1)
    
    def test_handles_last_successful_run_id_edge_case_empty(self):
        self.db.get_last_successful_run_id() |should| be(None)
    
    def test_handles_last_successful_run_id_edge_case_only_failures(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, result='F')
        self.db.finish_run(True)
        self.db.get_last_successful_run_id() |should| be(None)
    
    def test_can_clean_history(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        self.add_result(name)
        self.db.clean_history()
        self.db.total_runs |should| be(1)
    
    def test_cleans_history_when_finishing_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name)
        self.db.finish_run(True)
        self.add_result(name)
        self.db.finish_run(True)
        self.db.total_runs |should| be(1)
    
    def test_does_not_clean_history_after_unsuccessful_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, result='.')
        self.db.finish_run(True)
        self.add_result(name, result='F')
        self.db.finish_run(True)
        self.db.total_runs |should| be(2)
    
    def test_does_not_clean_history_after_partial_run(self):
        name = 'test_name (that.SpecialTest)'
        self.add_result(name, result='.')
        self.db.finish_run(True)
        self.add_result(name, result='.')
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
        self.db.get_last_run_id() |should| equal_to(run['id'])
    
    def test_knows_id_of_last_successful_full_run(self):
        name = 'test_name_%d (that.SpecialTest)'
        self.add_result(name % 1, result='.')
        run_1 = self.db.finish_run(True)
        self.add_result(name % 2, result='.')
        run_2 = self.db.finish_run(False)
        self.add_result(name % 3, result='F')
        run_3 = self.db.finish_run(True)
        self.db.get_last_successful_full_run_id() |should| equal_to(run_1['id'])
    
    def test_can_collect_tests_with_certain_result_after_certain_run(self):
        name = 'test_name_%d (that.SpecialTest)'
        run_ids = []
        for i, result in enumerate('.FExFus'):
            self.add_result(name % i, result=result)
            run_ids.append(self.db.finish_run(True)['id'])
        
        results = list(self.db.collect_results_after(run_ids[0], 'F'))
        results |should| equal_to(['test_name_1 (that.SpecialTest)', 'test_name_4 (that.SpecialTest)'])
        
        results = list(self.db.collect_results_after(run_ids[2], 'F'))
        results |should| equal_to(['test_name_4 (that.SpecialTest)'])
        
        results = list(self.db.collect_results_after(run_ids[4], 'F'))
        results |should| be_empty

#.............................................................................
#   test_db.py
