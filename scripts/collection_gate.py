"""Avoid repeating a collection when hosting and GitHub schedules overlap."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def should_collect(event, ref, generated_at, now, message=''):
    if event == 'workflow_dispatch' or (event == 'push' and ref == 'refs/heads/main'):
        return True, 'Explicit run or source configuration update.'
    if event == 'push' and ref == 'refs/heads/hostinger-trigger' and '[force-collection]' in message:
        return True, 'Explicit end-to-end hosting verification.'
    try:
        stamp = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        age = (now - stamp).total_seconds()
        if 0 <= age < 3300:
            return False, f'Existing collection is only {int(age / 60)} minutes old.'
    except (ValueError, TypeError, AttributeError):
        pass
    return True, 'Collection is missing or at least 55 minutes old.'


if __name__ == '__main__':
    path = Path('data/latest.json')
    try:
        generated = json.loads(path.read_text(encoding='utf-8')).get('generated_at')
    except (OSError, ValueError):
        generated = None
    collect, reason = should_collect(os.environ.get('GITHUB_EVENT_NAME'), os.environ.get('GITHUB_REF'), generated,
        datetime.now(timezone.utc), os.environ.get('REQUEST_MESSAGE', ''))
    print(reason)
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
        f.write(f'collect={str(collect).lower()}\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(f'## Collection gate\n\n{reason}\n\n')
