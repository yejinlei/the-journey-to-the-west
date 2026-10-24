import json
from pathlib import Path

d = json.loads(Path('06_Web前端/data/read/gubao.json').read_text(encoding='utf-8'))
for ch in d:
    if ch.get('l') in ('第98回', '第99回', '第100回'):
        print(f"\n=== ch={ch['l']}  p={ch['p']}  t={ch.get('t','')} ===")
        for ln in ch['lines'][:5]:
            print(f"  i={ln['i']}  t={ln['t']}  x={ln.get('x','')[:80]!r}")
            print(f"              z={ln.get('z','')[:80]!r}")
        print(f"  ... 共 {len(ch['lines'])} 行")
