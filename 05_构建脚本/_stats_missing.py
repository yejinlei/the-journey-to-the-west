# -*- coding: utf-8 -*-
import json
from collections import defaultdict, Counter

d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))

# lines 表按 (edition, form_type) 统计 text_zh 覆盖
stat = defaultdict(lambda: {'total': 0, 'zh': 0})
for l in d['lines']:
    k = (l.get('edition'), l.get('form_type'))
    stat[k]['total'] += 1
    if l.get('text_zh'):
        stat[k]['zh'] += 1

# annotations 表也统计
astat = defaultdict(lambda: {'total': 0, 'zh': 0})
for a in d['annotations']:
    k = (a.get('edition'), a.get('form_type'))
    astat[k]['total'] += 1
    if a.get('text_zh'):
        astat[k]['zh'] += 1

print('=== lines 表 ===')
for (ed, ft), c in sorted(stat.items()):
    miss = c['total'] - c['zh']
    print(f'{ed:20s} {ft:12s} total={c["total"]:5d} zh={c["zh"]:5d} miss={miss:5d}')

print()
print('=== annotations 表 ===')
for (ed, ft), c in sorted(astat.items()):
    miss = c['total'] - c['zh']
    print(f'{ed:20s} {ft:12s} total={c["total"]:5d} zh={c["zh"]:5d} miss={miss:5d}')

# 汇总：每个版本总缺多少
print()
print('=== 每个版本合计缺译（正文类，排除评点）===')
BODY_TYPES = {'main', 'verse', 'poem', 'title', 'caption'}
by_ed = defaultdict(int)
for (ed, ft), c in stat.items():
    if ft in BODY_TYPES:
        by_ed[ed] += c['total'] - c['zh']
for ed, miss in sorted(by_ed.items()):
    print(f'{ed:20s} 正文缺={miss:5d}')

print()
print('=== 每个版本评点类缺译 ===')
PING_TYPES = {'commentary', 'colophon', 'side', 'inline', 'top', 'bottom'}
by_ed = defaultdict(int)
for (ed, ft), c in stat.items():
    if ft in PING_TYPES:
        by_ed[ed] += c['total'] - c['zh']
for (ed, ft), c in astat.items():
    by_ed[ed] += c['total'] - c['zh']
for ed, miss in sorted(by_ed.items()):
    print(f'{ed:20s} 评点缺={miss:5d}')
