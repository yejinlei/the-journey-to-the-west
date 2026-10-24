# -*- coding: utf-8 -*-
"""输出到文件检查"""
import json
from pathlib import Path

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
lines = [l for l in d['lines']
         if l.get('edition') == 'baihui_xiangzhu'
         and l.get('form_type') == 'commentary']

out = []
out.append(f'total: {len(lines)}')
empty_zh = [l for l in lines if not l.get('text_zh')]
out.append(f'empty text_zh: {len(empty_zh)}')
same_as_src = [l for l in lines if l.get('text_zh') and l['text_zh'] == l.get('text')]
out.append(f'same as source: {len(same_as_src)}')

# 每 5 行输出一个样本
for i, l in enumerate(lines[:10]):
    out.append(f'--- line {i}: p{l["page_no"]}i{l["line_idx"]} ---')
    out.append(f'  SRC: {l["text"][:150]}')
    zh = l.get('text_zh', '(空)')
    out.append(f'  ZH:  {zh[:150]}')

Path('_bh_comm_check.txt').write_text('\n'.join(out), encoding='utf-8')
print('done')
