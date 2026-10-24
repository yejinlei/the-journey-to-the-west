# -*- coding: utf-8 -*-
"""抽样评点看长度与风格"""
import json, random
random.seed(42)
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
PINGS = {'xiyou_yuanzhi', 'baihui_xiangzhu', 'xinke_pingbi'}
FT = {'commentary', 'colophon', 'side', 'inline', 'top', 'bottom', 'title', 'poem', 'caption'}
by_ed = {}
for L in d['lines']:
    if L.get('edition') in PINGS and L.get('form_type') in FT:
        by_ed.setdefault(L['edition'], []).append(L)
for ed, rows in by_ed.items():
    print(f'\n=== {ed} ({len(rows)} rows) samples ===')
    for L in random.sample(rows, min(3, len(rows))):
        t = L.get('text', '')[:120].replace('\n', ' ')
        print(f"  p{L['page_no']} L{L['line_idx']} [{L['form_type']}]: {t}")
# annotations 表也看几条
print('\n=== xinke_pingbi annotations samples ===')
anns = [L for L in d['annotations'] if L.get('edition') == 'xinke_pingbi']
print(f'total: {len(anns)}')
for L in random.sample(anns, min(3, len(anns))):
    t = L.get('text', '')[:120].replace('\n', ' ')
    print(f"  p{L.get('page_no')} L{L.get('line_idx')} [{L.get('form_type')}]: {t}")
