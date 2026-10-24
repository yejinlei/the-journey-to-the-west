# -*- coding: utf-8 -*-
src = open('_xkb_batch3.py', encoding='utf-8').read()
# extract PAGES dict portion
start = src.index('PAGES = {}')
end = src.index('result = []')
code = src[start:end]
ns = {}
exec(code, ns)
PAGES = ns['PAGES']
for pn in sorted(PAGES.keys()):
    info = PAGES[pn]
    t = sum(info['widths'])
    l = len(info['text'])
    print(f'p{pn}: len={l} target={t} diff={l-t}')
