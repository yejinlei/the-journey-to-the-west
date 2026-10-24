# -*- coding: utf-8 -*-
import json, sys

data = json.load(open('_xkb_batch5.json','r',encoding='utf-8'))
merged = open('_xkb_merged.txt','r',encoding='utf-8').read()
import re
pages = {}
for m in re.finditer(r'## p(\d+)\nLINE_COUNT (\d+)\nLINE_WIDTHS \[(.*?)\]\n---\n(.*?)(?=\n===\n\n|\Z)', merged, re.DOTALL):
    p = int(m.group(1))
    w = [int(x) for x in m.group(3).split(',')]
    body = m.group(4).strip()
    pages[p] = (w, body)

all_ok = True
for entry in data:
    p = entry['page']
    w, body = pages[p]
    src = ''.join(entry['text_zh'])
    src_len = len(src)
    target = sum(w)
    widths_ok = (len(entry['widths']) == len(w)) and entry['widths'] == w
    lengths = [len(l) for l in entry['text_zh']]
    lengths_ok = lengths == w
    status = 'OK' if (widths_ok and lengths_ok and src_len==target) else 'FAIL'
    if status=='FAIL':
        all_ok=False
    print(f'p{p} src_len={src_len} target={target} lines_ok={lengths_ok} widths_ok={widths_ok} {status}')
    if lengths_ok is False:
        for i,(a,b) in enumerate(zip(lengths,w)):
            if a!=b:
                print(f'  line {i}: got {a} want {b}')
print('ALL OK' if all_ok else 'HAS FAILURES')
