# -*- coding: utf-8 -*-
"""Dump missing translations for a given edition (form_type=main|verse)."""
import json
import sys
from pathlib import Path

EDITION = sys.argv[1] if len(sys.argv) > 1 else 'xiyouji_zhuan'
PAGES = sys.argv[2] if len(sys.argv) > 2 else None  # e.g. "9-13"

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
lines = []
for l in d['lines']:
    if l.get('edition') != EDITION:
        continue
    if l.get('form_type') not in ('main', 'verse'):
        continue
    if l.get('text_zh'):
        continue
    if PAGES:
        a, b = PAGES.split('-')
        if not (int(a) <= l['page_no'] <= int(b)):
            continue
    lines.append(l)

for l in lines:
    print(f"[{l['page_no']},{l['line_idx']}] === {l['form_type']}")
    print(l['text'])
    print('---')
print(f"\n共 {len(lines)} 行")
