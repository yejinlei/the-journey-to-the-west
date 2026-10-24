# -*- coding: utf-8 -*-
"""Iteratively edit each page's text to exact target length."""
import json, re

TARGETS = {
    35: 485, 37: 447, 38: 484, 40: 452, 41: 483,
    42: 378, 45: 459, 46: 453, 48: 411
}

# Load source text for reference
src = open('_xkb_merged.txt', encoding='utf-8').read()
src_texts = {}
for m in re.finditer(r'## p(\d+)\nLINE_COUNT \d+\nLINE_WIDTHS (\[[^\]]+\])\n---\n(.*?)\n===', src, re.S):
    pn = int(m.group(1))
    if pn in TARGETS:
        src_texts[pn] = m.group(3)

for pn in sorted(TARGETS.keys()):
    st = src_texts[pn]
    print(f'p{pn} target={TARGETS[pn]}  source_len={len(st)}')
