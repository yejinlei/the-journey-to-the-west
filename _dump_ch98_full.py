import json
from pathlib import Path

d = json.loads(Path('06_Web前端/data/read/gubao.json').read_text(encoding='utf-8'))
for ch in d:
    if ch.get('l') in ('第98回', '第99回', '第100回'):
        print(f"\n=== ch={ch['l']}  p={ch['p']}  title_t={ch.get('t','')}  lines={len(ch['lines'])} ===")
        for ln in ch['lines'][:6]:
            x = ln.get('x','')
            z = ln.get('z','')
            print(f"  i={ln['i']} t={ln['t']!r}")
            print(f"    x={x[:120]!r}")
            print(f"    z={z[:120]!r}")
