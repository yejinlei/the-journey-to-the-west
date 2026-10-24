# -*- coding: utf-8 -*-
"""Print exact target widths and current text lengths per page"""
import re
src = open('_xkb_batch3.py', encoding='utf-8').read()
start = src.index('PAGES = {}')
end = src.index('result = []')
code = src[start:end]
ns = {}
exec(code, ns)
PAGES = ns['PAGES']

for pn in sorted(PAGES.keys()):
    info = PAGES[pn]
    w = info['widths']
    t = sum(w)
    l = len(info['text'])
    diff = l - t
    print(f'p{pn}: widths_sum={t} len={l} diff={diff}  nlines={len(w)}')
