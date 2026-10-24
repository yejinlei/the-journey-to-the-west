import json
from pathlib import Path

GUBAO = Path('06_Web前端/data/read/gubao.json')
d = json.loads(GUBAO.read_text(encoding='utf-8'))
print("top-level type:", type(d).__name__)
if isinstance(d, list):
    print("list len:", len(d))
    for i, l in enumerate(d):
        if not isinstance(l, dict): continue
        for fld in ('text', 'text_zh'):
            v = l.get(fld) or ''
            if 'notes' in v or '}}' in v or 'author =' in v or 'previous =' in v or 'next =' in v:
                print(f"  [{i}] p{l.get('page_no')}#{l.get('line_idx')} {fld}: {v[:200]}")
elif isinstance(d, dict):
    print("keys:", list(d.keys())[:10])
