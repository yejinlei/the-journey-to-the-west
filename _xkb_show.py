# -*- coding: utf-8 -*-
"""Show current text lengths and diff for each page"""
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
    print(f'p{pn}: target={t} len={l} diff={l-t}')
