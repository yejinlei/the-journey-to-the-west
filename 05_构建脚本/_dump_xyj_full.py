# -*- coding: utf-8 -*-
"""导出 xiyouji_zhuan 待翻译全部完整原文"""
import json
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
for l in d['lines']:
    if l.get('edition') != 'xiyouji_zhuan': continue
    if l.get('form_type') not in ('main','verse'): continue
    if l.get('text_zh'): continue
    print(f"[{l['page_no']},{l['line_idx']}] === {l['form_type']}")
    print(l['text'])
    print("---")
