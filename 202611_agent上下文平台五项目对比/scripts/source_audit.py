"""Audit recovered pinned source texts; static check, not upstream runtime test."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    records=json.loads((ROOT/'intermediate/源码清单.json').read_text())
    snapshots=json.loads((ROOT/'intermediate/仓库快照.json').read_text())
    output=ROOT/'intermediate/源码核对.json'
    expected={(r['repo'],r['path']):r['sha256'] for r in json.loads(output.read_text())['files']} if output.exists() else {}
    result=[]
    for item in records:
        path=ROOT/item['local']
        text=path.read_text()
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert item['commit']==snapshots[item['project']]['sha']
        if (item['repo'],item['path']) in expected:
            assert digest==expected[(item['repo'],item['path'])],path
        row={k:item[k] for k in ('repo','commit','path','url')}
        row.update(sha256=digest,bytes=path.stat().st_size,lines=len(text.splitlines()))
        if path.suffix=='.py':
            tree=ast.parse(text)
            row['top_level_symbols']=[n.name for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))]
        result.append(row)
    output.write_text(json.dumps({'checked_at':'2026-11-17','scope':'固定文本散列/版本/语法；不是五框架测试','files':result},ensure_ascii=False,indent=2)+'\n')
    print(f'PASS: {len(result)} fixed source files')


if __name__=='__main__':
    main()
