import json
from pathlib import Path

print("=== docs/data/pages/read.json ===")
d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
for l in d['lines']:
    if l.get('edition') == 'gubao':
        for fld in ('text', 'text_zh'):
            v = l.get(fld) or ''
            if '尽三三行' in v or '盡三三行' in v or 'notes' in v or '}}' in v:
                print(f"  p{l['page_no']}#{l['line_idx']} {fld}: {v!r}")

print("\n=== 06_Web前端/data/read/gubao.json ===")
d2 = json.loads(Path('06_Web前端/data/read/gubao.json').read_text(encoding='utf-8'))
print(f"  type: {type(d2).__name__}, len: {len(d2)}")
bad = 0
for ch in d2:
    for ln in ch.get('lines', []):
        for fld in ('x', 'z'):
            v = ln.get(fld) or ''
            if '尽三三行' in v or '盡三三行' in v or 'notes' in v or '}}' in v:
                print(f"  ch={ch['l']} p{ch['p']}#{ln['i']} {fld}: {v!r}")
                bad += 1
print(f"  bad count: {bad}")

print("\n=== 06_Web前端/data/read/gubao.json 前两章 line[0] 示例 ===")
for ch in d2[:3]:
    if ch.get('lines'):
        ln0 = ch['lines'][0]
        print(f"  ch={ch['l']} p{ch['p']}: {ln0}")
