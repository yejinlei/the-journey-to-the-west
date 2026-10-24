# -*- coding: utf-8 -*-
"""检查 xinke_pingbi poem 是否在 gubao 已有翻译"""
import json
from pathlib import Path

data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
lines = data['lines']

# 建立 gubao 文本 -> text_zh 的字典（前 15 字做 key）
gb = {}
for l in lines:
    if l.get('edition') == 'gubao' and l.get('text_zh'):
        key = l['text'].strip()[:15]
        gb.setdefault(key, l['text_zh'])

xk_poems = [l for l in lines if l.get('edition') == 'xinke_pingbi'
            and l.get('form_type') in ('poem', 'verse', 'caption', 'inline')]
matched = 0
unmatched = []
for l in xk_poems:
    key = l['text'].strip()[:15]
    if key in gb:
        matched += 1
    else:
        unmatched.append((l['page_no'], l['line_idx'], l['form_type'], l['text'][:60]))

print(f'matched: {matched}, unmatched: {len(unmatched)}')
print('\n未匹配：')
for row in unmatched:
    print(row)
