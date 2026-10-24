# -*- coding: utf-8 -*-
"""Iteratively tune text lengths."""
import re

merged = open('_xkb_merged.txt','r',encoding='utf-8').read()
widths_map = {}
for m in re.finditer(r'## p(\d+)\nLINE_COUNT (\d+)\nLINE_WIDTHS \[(.*?)\]\n---', merged):
    p = int(m.group(1))
    widths_map[p] = [int(x) for x in m.group(3).split(',')]

targets = {p: sum(w) for p, w in widths_map.items() if p in (63,65,66,67,69)}

# Source text lengths
sources = {}
for m in re.finditer(r'## p(\d+)\n.*?\n.*?\n---\n(.*?)(?=\n===)', merged, re.DOTALL):
    p = int(m.group(1))
    if p in targets:
        sources[p] = m.group(2).strip()

for p in [63, 65, 66, 67, 69]:
    print(f'p{p}: target={targets[p]}, source_len={len(sources[p])}')
