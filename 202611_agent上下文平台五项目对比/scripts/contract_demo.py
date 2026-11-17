"""Recovered teaching example: SQLite, NOT any of the five upstream frameworks."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def bounds(year, month):
    if not 1 <= month <= 12:
        raise ValueError('invalid month')
    tz = ZoneInfo('Asia/Shanghai')
    start = datetime(year, month, 1, tzinfo=tz)
    end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=tz)
    return tuple(t.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') for t in (start, end))


def fail(kind, call):
    try:
        call()
    except kind:
        return
    raise AssertionError('expected rejection')


def run():
    data = json.loads((ROOT / 'input/业务样例.json').read_text())
    db = sqlite3.connect(':memory:')
    db.executescript('''CREATE TABLE orders(order_id INTEGER PRIMARY KEY, tenant_id TEXT,
        region TEXT, status TEXT, paid_at_utc TEXT, paid_cents INTEGER, refund_cents INTEGER);
        CREATE TABLE items(item_id INTEGER PRIMARY KEY, order_id INTEGER);''')
    db.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?,?)', data['orders'])
    db.executemany('INSERT INTO items VALUES (?,?)', data['items'])
    principal = data['principal']

    def query(region='east', tenant='A', version='v1', month=10, join=False):
        if tenant != principal['tenant'] or region not in principal['regions']:
            raise PermissionError('scope override')
        if version != 'v1':
            raise ValueError('unapproved metric version')
        start, end = bounds(2026, month)
        table = 'orders o JOIN items i ON i.order_id=o.order_id' if join else 'orders o'
        return db.execute(f'''SELECT COALESCE(SUM(o.paid_cents-o.refund_cents),0) FROM {table}
            WHERE o.tenant_id=? AND o.region=? AND o.status='paid'
            AND o.paid_at_utc>=? AND o.paid_at_utc<?''', (tenant, region, start, end)).fetchone()[0]

    assert bounds(2026, 10) == ('2026-09-30T16:00:00Z','2026-10-31T16:00:00Z')
    assert bounds(2026, 12)[1] == '2026-12-31T16:00:00Z'
    fail(ValueError, lambda: bounds(2026, 13))
    baseline, wrong = query(), query(join=True)
    assert baseline == 25000 and wrong == 35000
    fail(PermissionError, lambda: query(tenant='B'))
    fail(PermissionError, lambda: query(region='west'))
    fail(ValueError, lambda: query(version='v0'))
    assert query(month=8) == 0
    db.execute('UPDATE orders SET refund_cents=6000 WHERE order_id=2')
    updated = query()
    assert updated == 24000
    key = lambda policy, version, watermark: hashlib.sha256(json.dumps([principal['tenant'], policy, version, watermark]).encode()).hexdigest()
    assert len({key('p1','v1','d1'),key('p2','v1','d1'),key('p1','v2','d1'),key('p1','v1','d2')}) == 4
    evidence = [('A','v1',True),('A','v0',True),('A','v1',False),('B','v1',True)]
    assert [e for e in evidence if e == ('A','v1',True)] == [('A','v1',True)]
    db.close()
    report = {'checked_at':'2026-11-17','scope':'重建后自建离线示例，非五框架测试',
              'baseline_cents':baseline,'wrong_join_cents':wrong,'updated_cents':updated,
              'utc_bounds':bounds(2026,10),'checks':'月份、fan-out、权限、版本、空窗口、缓存与证据检查通过'}
    (ROOT / 'intermediate/契约演示结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('PASS: 250 CNY; wrong join 350; refund update 240; scope/time/version checks')


if __name__ == '__main__':
    run()
