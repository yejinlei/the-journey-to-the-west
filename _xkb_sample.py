# -*- coding: utf-8 -*-
"""抽样 xinke_pingbi 的 text_zh 质量"""
import json
d = json.load(open('docs/data/pages/read.json', 'r', encoding='utf-8'))
for page in [4, 8, 15, 25, 40, 55, 67, 69]:
    rows = [l for l in d['lines'] if l.get('edition')=='xinke_pingbi' and l.get('form_type')=='main' and l['page_no']==page]
    rows.sort(key=lambda l: l['line_idx'])
    print(f'\n========== p{page} ({len(rows)} rows) ==========')
    for l in rows[:5]:
        print(f'--- [{l["line_idx"]}] ---')
        print('SRC:', l['text'][:80])
        print('ZH :', l['text_zh'][:80])
    if len(rows) > 5:
        print(f'... ({len(rows)-5} more rows)')
        last = rows[-1]
        print(f'--- [{last["line_idx"]}] ---')
        print('SRC:', last['text'][:80])
        print('ZH :', last['text_zh'][:80])
