"""Fetch pinned public texts, respecting environment proxy and normal TLS. Network required."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]


def main():
    items=json.loads((ROOT/'intermediate/源码清单.json').read_text())
    expected={(r['repo'],r['path']):r['sha256'] for r in json.loads((ROOT/'intermediate/源码核对.json').read_text())['files']}
    for item in items:
        url=f"https://raw.githubusercontent.com/{item['repo']}/{item['commit']}/{item['path']}"
        with urlopen(Request(url,headers={'User-Agent':'llm-learn-source-review'}),timeout=60) as response:
            text=response.read().decode('utf-8').replace('\r\n','\n').rstrip('\n')+'\n'
        assert hashlib.sha256(text.encode()).hexdigest()==expected[(item['repo'],item['path'])],item['path']
        p=ROOT/item['local'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        print('OK',item['repo'],item['path'])


if __name__=='__main__':
    main()
