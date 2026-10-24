# -*- coding: utf-8 -*-
"""检查 gubao page 100（第100回）"""
import json
from pathlib import Path

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))

lines = [l for l in d['lines']
         if l.get('edition') == 'gubao'
         and l.get('form_type') == 'main'
         and l.get('page_no') == 100]

out = [f'gubao page 100 main 行数: {len(lines)}']
for i, l in enumerate(lines[:5]):
    src = l.get('text', '')
    zh = l.get('text_zh', '')
    same = '同' if src == zh else '异'
    out.append(f'--- 第{i+1}行 p{l["page_no"]}i{l["line_idx"]} [{same}] ---')
    out.append(f'  SRC: {src}')
    out.append(f'  ZH:  {zh}')
Path('_gubao_ch100.txt').write_text('\n'.join(out), encoding='utf-8')
print(f'gubao page 100 main 行数: {len(lines)}')
