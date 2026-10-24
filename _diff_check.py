# -*- coding: utf-8 -*-
"""细看 gubao text_zh vs OpenCC(text) 差异"""
import json
from pathlib import Path
from opencc import OpenCC

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
cc = OpenCC('t2s')

lines = [l for l in d['lines']
         if l.get('edition') == 'gubao'
         and l.get('form_type') == 'main'
         and l.get('page_no') == 100]

out = []
for l in lines[:5]:
    src = l['text']
    zh = l['text_zh']
    oc = cc.convert(src)
    out.append(f'=== p{l["page_no"]}i{l["line_idx"]} ===')
    out.append(f'SRC: {src}')
    out.append(f'OC : {oc}')
    out.append(f'ZH : {zh}')
    out.append(f'OC==ZH? {oc == zh}')
    # 找差异字符
    diffs = []
    for i, (a, b) in enumerate(zip(oc, zh)):
        if a != b:
            diffs.append((i, a, b))
    out.append(f'OC↔ZH 差异({len(diffs)}): {diffs[:20]}')
    out.append('')

Path('_diff_sample.txt').write_text('\n'.join(out), encoding='utf-8')
print(f'saved to _diff_sample.txt')
