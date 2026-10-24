# -*- coding: utf-8 -*-
"""dump xinke_pingbi 分批"""
import json
import sys
from pathlib import Path

a, b = int(sys.argv[1]), int(sys.argv[2])
out_path = Path(sys.argv[3])

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
lines = [l for l in d['lines']
         if l.get('edition') == 'xinke_pingbi'
         and l.get('form_type') in ('main','verse','title','poem')
         and a <= l['page_no'] <= b]

lines.sort(key=lambda l: (l['page_no'], l['line_idx']))

with out_path.open('w', encoding='utf-8') as f:
    for l in lines:
        f.write(f"[{l['page_no']},{l['line_idx']}] === {l['form_type']}\n")
        f.write(l['text'] + "\n---\n")
    f.write(f"\n共 {len(lines)} 行\n")
print(f'dumped {len(lines)} lines to {out_path}')
