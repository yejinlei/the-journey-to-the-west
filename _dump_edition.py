# -*- coding: utf-8 -*-
"""批量 dump 指定 edition 的未翻译原文"""
import json
import sys
from pathlib import Path

EDITION = sys.argv[1]
PAGES = sys.argv[2]
OUT = Path(sys.argv[3])

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
a, b = PAGES.split('-')
a, b = int(a), int(b)
lines = []
for l in d['lines']:
    if l.get('edition') != EDITION:
        continue
    if l.get('form_type') not in ('main','verse'):
        continue
    if l.get('text_zh'):
        continue
    if not (a <= l['page_no'] <= b):
        continue
    lines.append(l)

with OUT.open('w', encoding='utf-8') as f:
    for l in lines:
        f.write(f"[{l['page_no']},{l['line_idx']}] === {l['form_type']}\n")
        f.write(l['text'] + "\n")
        f.write("---\n")
    f.write(f"\n共 {len(lines)} 行\n")
print(f'dumped {len(lines)} lines to {OUT}')
