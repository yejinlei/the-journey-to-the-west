# -*- coding: utf-8 -*-
"""清空 xinke_pingbi lines 表的 text_zh，annotations 不动"""
import json
from collections import Counter
from pathlib import Path

p = Path('docs/data/pages/read.json')
d = json.loads(p.read_text(encoding='utf-8'))

# 先看结构
lines_xkb = [l for l in d['lines'] if l.get('edition') == 'xinke_pingbi']
anno_xkb = [a for a in d.get('annotations', []) if a.get('edition') == 'xinke_pingbi']

print(f'xinke_pingbi in lines: {len(lines_xkb)}')
print(f'xinke_pingbi in annotations: {len(anno_xkb)}')

c = Counter(l.get('form_type') for l in lines_xkb)
print(f'lines form_type: {dict(c)}')

# 哪些在 annotations 表里已经翻过 text_zh
anno_done = sum(1 for a in anno_xkb if a.get('text_zh'))
print(f'annotations 已翻: {anno_done}/{len(anno_xkb)}')

# 只清 lines 表
cleared = 0
for l in lines_xkb:
    if l.get('text_zh'):
        l['text_zh'] = ''
        cleared += 1
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'cleared lines: {cleared}')
