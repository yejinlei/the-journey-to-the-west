# -*- coding: utf-8 -*-
"""检查 xinke_pingbi 每页行数"""
import json
from collections import defaultdict
from pathlib import Path

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))

by_page = defaultdict(int)
for l in d['lines']:
    if l.get('edition') != 'xinke_pingbi': continue
    if l.get('form_type') not in ('main','verse','title','poem'): continue
    by_page[l['page_no']] += 1

for pn in sorted(by_page):
    print(f'  page {pn}: {by_page[pn]}')

# 检查每行平均长度
lines = [l for l in d['lines']
         if l.get('edition') == 'xinke_pingbi'
         and l.get('form_type') in ('main','verse','title','poem')]
lengths = [len(l['text']) for l in lines]
print(f'\n平均行长: {sum(lengths)/len(lengths):.1f}')
print(f'总字数: {sum(lengths)}')
