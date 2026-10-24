# -*- coding: utf-8 -*-
"""Investigate the format used."""
import json
d = json.load(open('_xkb_batch1.json','r',encoding='utf-8'))
print(f'Total entries: {len(d)}')
for e in d:
    t = e['text_zh']
    print(f"p{e['page']}: type={type(t).__name__}, len(text_zh)={len(t)}, widths_sum={sum(e['widths'])}, diff={len(t)-sum(e['widths'])}")
