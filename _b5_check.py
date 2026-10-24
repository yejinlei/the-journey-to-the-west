# -*- coding: utf-8 -*-
"""Interactive check/adjust tool."""
import json, re, sys

merged = open('_xkb_merged.txt','r',encoding='utf-8').read()
widths_map = {}
for m in re.finditer(r'## p(\d+)\nLINE_COUNT (\d+)\nLINE_WIDTHS \[(.*?)\]\n---', merged):
    p = int(m.group(1))
    widths_map[p] = [int(x) for x in m.group(3).split(',')]

from _b5_texts import texts

for p in [63, 65, 66, 67, 69]:
    w = widths_map[p]
    t = texts[p]
    print(f'p{p}: len={len(t)}, target={sum(w)}, diff={len(t)-sum(w):+d}')
