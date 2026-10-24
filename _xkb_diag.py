# -*- coding: utf-8 -*-
"""Diagnose each page: show text length and quote character usage"""
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
    # count ASCII quotes and Chinese quotes
    aq = info['text'].count(chr(0x27))  # '
    dq = info['text'].count(chr(0x22))  # "
    csl = info['text'].count('\u2018')  # '
    csr = info['text'].count('\u2019')  # '
    cdq = info['text'].count('\u201c') + info['text'].count('\u201d')
    print(f'p{pn}: target={t} len={l} diff={l-t} | ASCII: {aq} single {dq} double | CJK: {csl+csr} single {cdq} double')
