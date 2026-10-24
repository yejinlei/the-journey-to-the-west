# -*- coding: utf-8 -*-
"""检查所有 edition 的 text_zh 质量：字面转换 vs 真白话"""
import json
from collections import defaultdict
from pathlib import Path
from opencc import OpenCC

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
cc = OpenCC('t2s')

# 对每个 edition，比较 text_zh 与 OpenCC(t2s)(text)
stats = defaultdict(lambda: {'total': 0, 'literal_only': 0, 'translated': 0, 'empty': 0})

for l in d['lines']:
    ed = l.get('edition')
    ft = l.get('form_type')
    zh = l.get('text_zh')
    src = l.get('text', '')
    # 只统计正文/评点
    if ft not in ('main', 'verse', 'title', 'poem', 'commentary', 'colophon'):
        continue
    if not zh:
        stats[ed]['empty'] += 1
        continue
    stats[ed]['total'] += 1
    expected = cc.convert(src)
    if zh == expected:
        stats[ed]['literal_only'] += 1
    else:
        stats[ed]['translated'] += 1

out = []
out.append(f'{"edition":<20} {"total":>7} {"字面":>7} {"改写":>7} {"空":>7} {"字面比":>8}')
out.append('-' * 60)
for ed, s in sorted(stats.items()):
    ratio = f"{s['literal_only']/s['total']*100:.1f}%" if s['total'] else '-'
    out.append(f'{ed:<20} {s["total"]:>7} {s["literal_only"]:>7} {s["translated"]:>7} {s["empty"]:>7} {ratio:>8}')

Path('_quality_check.txt').write_text('\n'.join(out), encoding='utf-8')
print('\n'.join(out))
