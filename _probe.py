# -*- coding: utf-8 -*-
"""Verify text_zh is a continuous string with len == sum(widths)."""
import json, re
d = json.load(open('_xkb_batch1.json','r',encoding='utf-8'))
for e in d[:3]:
    t = e['text_zh']
    print(f"p{e['page']} type={type(t).__name__} len={len(t)} widths_sum={sum(e['widths'])} match={len(t)==sum(e['widths'])}")
