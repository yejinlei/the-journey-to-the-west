import json
from pathlib import Path

d = json.loads(Path('06_Web前端/data/read/gubao.json').read_text(encoding='utf-8'))
for ch in d:
    if ch.get('l') in ('第98回', '第99回', '第100回'):
        print(f"\n===== ch={ch['l']}  p={ch['p']}  title_t={ch.get('t','')}  lines={len(ch['lines'])} =====")
        for k, ln in enumerate(ch['lines']):
            x = ln.get('x','')
            z = ln.get('z','')
            print(f"  --- line[{k}] i={ln['i']} t={ln['t']!r} c={ln.get('c',0)} ---")
            print(f"  x[:200]: {x[:200]!r}")
            print(f"  z[:200]: {z[:200]!r}")
