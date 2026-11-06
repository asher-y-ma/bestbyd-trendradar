import unittest
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import export_bestbyd as exporter
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

    def test_fresh_checkout_exports_without_preexisting_directories(self):
        now = datetime(2026, 11, 6, 14, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = root / '.runtime'
            (runtime / 'output/news').mkdir(parents=True)
            (root / 'config').mkdir()
            (root / 'config/topics.json').write_text('{"brand_byd":["BYD"]}')
            (root / 'upstream.json').write_text('{}')
            (runtime / 'output/index.html').write_text('<h1>Test report</h1>')
            with closing(sqlite3.connect(runtime / 'output/news/2026-11-06.db')) as db:
                db.executescript("CREATE TABLE platforms(id TEXT,name TEXT); CREATE TABLE crawl_records(id INTEGER,crawl_time TEXT); CREATE TABLE crawl_source_status(crawl_record_id INTEGER,platform_id TEXT,status TEXT); CREATE TABLE news_items(title TEXT,platform_id TEXT,rank INTEGER,url TEXT,mobile_url TEXT,last_crawl_time TEXT); INSERT INTO platforms VALUES('weibo','Weibo'); INSERT INTO crawl_records VALUES(1,'22:00'); INSERT INTO crawl_source_status VALUES(1,'weibo','success'); INSERT INTO news_items VALUES('BYD announces a new car','weibo',3,'https://weibo.com/a','','22:00');")
            with patch.object(exporter, 'ROOT', root):
                exporter.export(runtime, now)
            self.assertEqual(json.loads((root / 'data/latest.json').read_text())['collection']['matched_current'], 1)
            self.assertTrue((root / 'reports/latest.html').exists())


if __name__ == '__main__':
    unittest.main()
