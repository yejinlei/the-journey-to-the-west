# -*- coding: utf-8 -*-
"""
xinke_pingbi 评点类在 lines 表和 annotations 表中各存一份。
之前只在 lines 表写了 text_zh，annotations 表没写。
本脚本：把 lines 表中已有的 text_zh 同步到 annotations 表。
"""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')
data = json.loads(READ_JSON.read_text(encoding='utf-8'))

PING_TYPES = {'colophon', 'side', 'inline', 'top', 'bottom', 'caption'}

# 从 lines 表建立索引 (page_no, line_idx) -> text_zh
line_zh = {}
for l in data['lines']:
    if l.get('edition') != 'xinke_pingbi': continue
    if l.get('form_type') not in PING_TYPES: continue
    if l.get('text_zh'):
        line_zh[(l['page_no'], l['line_idx'])] = l['text_zh']

print(f'lines 表可用 zh: {len(line_zh)}')

# 同步到 annotations 表
synced = 0
miss = 0
for a in data['annotations']:
    if a.get('edition') != 'xinke_pingbi': continue
    k = (a['page_no'], a['line_idx'])
    if a.get('text_zh'):
        continue
    if k in line_zh:
        a['text_zh'] = line_zh[k]
        synced += 1
    else:
        miss += 1
        print(f'  MISS anno key={k} ft={a.get("form_type")} text={a.get("text","")[:60]}')

print(f'synced={synced}, miss={miss}')
READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
