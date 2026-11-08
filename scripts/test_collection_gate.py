import unittest
from datetime import datetime, timedelta, timezone
from collection_gate import should_collect


class CollectionGateTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 8, 6, tzinfo=timezone.utc)

    def test_fresh_scheduled_run_skips(self):
        self.assertFalse(should_collect('schedule', 'refs/heads/main', self.now.isoformat(), self.now)[0])

    def test_fresh_hosting_request_skips(self):
        self.assertFalse(should_collect('push', 'refs/heads/hostinger-trigger', self.now.isoformat(), self.now)[0])

    def test_explicit_hosting_verification_runs(self):
        self.assertTrue(should_collect('push', 'refs/heads/hostinger-trigger', self.now.isoformat(), self.now, '[force-collection]')[0])

    def test_stale_run_collects(self):
        self.assertTrue(should_collect('schedule', 'refs/heads/main', (self.now-timedelta(minutes=55)).isoformat(), self.now)[0])

    def test_invalid_time_collects(self):
        self.assertTrue(should_collect('schedule', 'refs/heads/main', 'invalid', self.now)[0])

    def test_manual_request_collects(self):
        self.assertTrue(should_collect('workflow_dispatch', 'refs/heads/main', self.now.isoformat(), self.now)[0])

    def test_source_update_collects(self):
        self.assertTrue(should_collect('push', 'refs/heads/main', self.now.isoformat(), self.now)[0])
