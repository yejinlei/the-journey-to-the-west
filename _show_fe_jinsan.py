import json
from pathlib import Path

d = json.loads(Path('06_Web前端/data/read/gubao.json').read_text(encoding='utf-8'))
# d is list of chapters, each with 'l' 't' 'p' 'lines' (each line has i,t,x,z,c)
bad = 0
for ch in d:
    for ln in ch.get('lines', []):
        for fld in ('x', 'z'):
            v = ln.get(fld) or ''
            if 'notes' in v or '}}' in v or 'author =' in v or 'previous =' in v or 'next =' in v or '尽三三行满道归根' in v or '盡三三行滿道歸根' in v:
                print(f"  ch={ch['l']} p{ch['p']}#{ln['i']} {fld}: {v!r}")
                bad += 1

print(f"\n残留条数: {bad}")
