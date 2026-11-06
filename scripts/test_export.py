import unittest
from datetime import datetime, timedelta, timezone
from export_bestbyd import canonical_url, relevant, merge_signals


class ExportChecks(unittest.TestCase):
    def test_topics(self):
        self.assertTrue(relevant('比亚迪发布全新车型'))
        self.assertTrue(relevant('腾势D9新版本'))
        self.assertTrue(relevant('海豹06新车上市'))
        self.assertFalse(relevant('海豹在海边休息'))
        self.assertFalse(relevant('张三发布新手机'))

    def test_source_hosts(self):
        self.assertEqual(canonical_url('https://www.douyin.com/hot/123#details', 'douyin'), 'https://www.douyin.com/hot/123')
        for url in ['http://weibo.com/test', 'https://weibo.com.evil.example/test', 'https://weibo.com@evil.example/test', 'https://weibo.com:8443/test']:
            self.assertIsNone(canonical_url(url, 'weibo'))

    def test_repeat_keeps_first_seen_and_expires_old_clues(self):
        now = datetime(2026, 11, 6, tzinfo=timezone.utc)
        old = {'id': 'a', 'title': '比亚迪发布车型', 'platform': 'weibo', 'url': 'https://weibo.com/a', 'rank': 4, 'first_seen': (now-timedelta(days=1)).isoformat(), 'last_seen': (now-timedelta(days=1)).isoformat()}
        expired = dict(old, id='b', last_seen=(now-timedelta(days=8)).isoformat())
        current = dict(old, first_seen=now.isoformat(), last_seen=now.isoformat(), rank=2)
        merged = merge_signals([old, expired], [current], now)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['first_seen'], old['first_seen'])
        self.assertEqual(merged[0]['rank'], 2)


if __name__ == '__main__':
    unittest.main()
