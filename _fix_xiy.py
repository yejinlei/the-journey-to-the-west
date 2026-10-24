# -*- coding: utf-8 -*-
"""xiyou_yuanzhi p1 上 7 行 '##' 为章节分隔符（非正文），标记为已处理。"""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')
data = json.loads(READ_JSON.read_text(encoding='utf-8'))

targets = {(1,1),(1,4),(1,7),(1,10),(1,13),(1,17),(1,22)}
idx = {}
for l in data['lines']:
    if l.get('edition') != 'xiyou_yuanzhi' or l.get('form_type') not in ('main','verse'):
        continue
    idx[(l['page_no'], l['line_idx'])] = l

missing = [k for k in targets if k not in idx]
assert not missing, f'not found keys: {missing}'

for k in targets:
    idx[k]['text_zh'] = '##'  # 原样保留分隔符

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'写入 {len(targets)} 行（分隔符，原样保留）')
