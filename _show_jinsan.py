import json
from pathlib import Path

for fp in ['docs/data/pages/read.json', '06_Web前端/data/read/gubao.json']:
    d = json.loads(Path(fp).read_text(encoding='utf-8'))
    lines = d if isinstance(d, list) else d['lines']
    print(f"\n=== {fp} ===")
    for l in lines:
        for fld in ('text', 'text_zh'):
            v = l.get(fld) or ''
            if '尽三三行' in v or '盡三三行' in v:
                print(f"  [{l.get('edition')}] p{l.get('page_no')}#{l.get('line_idx')} {fld}: {v!r}")
