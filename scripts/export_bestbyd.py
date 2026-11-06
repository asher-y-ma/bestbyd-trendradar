"""Export BYD-matching TrendRadar observations; titles are clues, never article facts."""
import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {
    'weibo': ('weibo.com', 'weibo.cn'), 'douyin': ('douyin.com',),
    'zhihu': ('zhihu.com',), 'bilibili-hot-search': ('bilibili.com',),
    'baidu': ('baidu.com',), 'toutiao': ('toutiao.com',),
    'thepaper': ('thepaper.cn',), 'cls-hot': ('cls.cn',),
}
BRAND = re.compile(r'比亚迪|\bBYD\b|腾势|\bDenza\b|方程豹|Fang.?Cheng.?Bao|仰望|\bYangwang\b', re.I)
MODEL = re.compile(r'海豹\s*(?:0[567]|DM|EV)|海狮\s*(?:0[5678]|DM|EV)|宋\s*(?:PLUS|PRO|L\s*DM)|秦\s*(?:PLUS|L\s*DM|L\s*EV)|元\s*(?:PLUS|UP)|[唐汉]\s*(?:DM|EV|L\s*DM)|豹\s*[578]|\bATTO\s*[123]\b|\bSEALION\s*[5678]\b', re.I)


def canonical_url(url, platform):
    try:
        u = urlsplit(url)
        host = (u.hostname or '').lower()
        allowed = any(host == h or host.endswith('.' + h) for h in HOSTS.get(platform, ()))
        if u.scheme != 'https' or u.username or u.password or u.port not in (None, 443) or not allowed:
            return None
        return urlunsplit(('https', u.netloc.lower(), u.path or '/', u.query, ''))
    except ValueError:
        return None


def relevant(title):
    return bool(BRAND.search(title) or MODEL.search(title))


def merge_signals(previous, current, now):
    cutoff = now - timedelta(days=7)
    merged = {}
    for item in previous:
        try:
            if datetime.fromisoformat(item['last_seen']) < cutoff:
                continue
            if not canonical_url(item['url'], item['platform']) or not relevant(item['title']):
                continue
            merged[item['id']] = item
        except (KeyError, TypeError, ValueError):
            continue
    for item in current:
        old = merged.get(item['id'])
        if old:
            item['first_seen'] = old['first_seen']
        merged[item['id']] = item
    return sorted(merged.values(), key=lambda x: (x['last_seen'], -x['rank']), reverse=True)[:500]


def export(runtime, now=None):
    now = now or datetime.now(timezone.utc)
    date = now.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d')
    db = runtime / 'output' / 'news' / (date + '.db')
    if not db.is_file():
        raise RuntimeError('TrendRadar did not create its current-day database.')
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        record = conn.execute('SELECT id, crawl_time FROM crawl_records ORDER BY id DESC LIMIT 1').fetchone()
        if not record:
            raise RuntimeError('TrendRadar recorded no completed collection.')
        statuses = [dict(x) for x in conn.execute('SELECT s.platform_id, p.name, s.status FROM crawl_source_status s JOIN platforms p ON p.id=s.platform_id WHERE s.crawl_record_id=?', (record['id'],))]
        if not any(x['status'] == 'success' for x in statuses):
            raise RuntimeError('All hotlist sources failed; previous exported data was preserved.')
        rows = [dict(x) for x in conn.execute('SELECT n.title,n.platform_id AS platform,n.rank,n.url,n.mobile_url,p.name AS platform_name FROM news_items n JOIN platforms p ON p.id=n.platform_id WHERE n.last_crawl_time=?', (record['crawl_time'],))]
    topics = json.loads((ROOT / 'config/topics.json').read_text(encoding='utf-8'))
    current = []
    for row in rows:
        title = re.sub(r'\s+', ' ', row['title']).strip()[:400]
        if not relevant(title):
            continue
        url = canonical_url(row['url'], row['platform']) or canonical_url(row['mobile_url'], row['platform'])
        if not url:
            continue
        current.append({'id': hashlib.sha256((row['platform'] + '|' + url).encode()).hexdigest(),
            'platform': row['platform'], 'platform_name': row['platform_name'], 'title': title,
            'url': url, 'rank': max(1, int(row['rank'])), 'first_seen': now.isoformat(),
            'last_seen': now.isoformat(), 'matched_terms': [key for key, patterns in topics.items() if any(re.search(p, title, re.I) for p in patterns)]})
    target = ROOT / 'data/latest.json'
    previous = json.loads(target.read_text(encoding='utf-8')).get('signals', []) if target.exists() else []
    signals = merge_signals(previous, current, now)
    result = {'schema_version': 1, 'project': 'bestbyd-trendradar', 'generated_at': now.isoformat(),
        'timezone': 'Asia/Shanghai', 'upstream': json.loads((ROOT / 'upstream.json').read_text()),
        'collection': {'status': 'ok' if all(x['status'] == 'success' for x in statuses) else 'degraded',
            'sources': statuses, 'total_items': len(rows), 'matched_current': len(current), 'retained_signals': len(signals)},
        'editorial_note': 'Hotlist observations identify topics, not verified facts or original publication dates. BestBYD requires source evidence before writing.',
        'signals': signals}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(target)
    report = runtime / 'output/index.html'
    if report.exists():
        (ROOT / 'reports').mkdir(parents=True, exist_ok=True)
        shutil.copyfile(report, ROOT / 'reports/latest.html')
    print(json.dumps(result['collection'], ensure_ascii=False))
    summary = __import__('os').environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write(f"## BYD monitoring\n\nCollected {len(rows)} hotlist entries; {len(current)} currently match BYD topics. Retained {len(signals)} observations.\n\n")
            for source in statuses:
                f.write(f"- {source['name']}: {source['status']}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    export(parser.parse_args().runtime.resolve())
