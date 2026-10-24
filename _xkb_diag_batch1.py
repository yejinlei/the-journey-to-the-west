# -*- coding: utf-8 -*-
"""诊断 batch1 是否真的白话改写"""
import json
from pathlib import Path
import re
import opencc

d = json.load(open('docs/data/pages/read.json','r',encoding='utf-8'))
by_key = {(l['page_no'], l['line_idx']): l for l in d['lines'] if l.get('edition')=='xinke_pingbi'}

batch1 = json.load(open('_xkb_batch1.json','r',encoding='utf-8'))
_T2S = opencc.OpenCC('t2s')

total = 0
lit_convert = 0  # 只字面转换
quotes_only = 0  # 字面 + 加引号
real_rewrite = 0  # 真白话
for entry in batch1:
    page = entry['page']
    zh = entry['text_zh']
    rows = sorted([l for l in by_key.values() if l['page_no']==page and l['form_type']=='main'], key=lambda l: l['line_idx'])
    # 拼原文
    src = ''.join(r['text'] for r in rows)
    src_simp = _T2S.convert(src)
    # 去掉引号后比较
    no_quote = re.sub(r"['\"]", '', zh)
    no_quote_src = re.sub(r"['\"]", '', src_simp)
    if no_quote == no_quote_src:
        quotes_only += 1
    elif no_quote != src_simp:
        # 看变化比例
        diff_chars = sum(1 for a,b in zip(no_quote, no_quote_src) if a!=b) + abs(len(no_quote)-len(no_quote_src))
        if diff_chars / max(len(src_simp), 1) < 0.05:
            quotes_only += 1  # 微小差异，视为字面
        else:
            real_rewrite += 1
    else:
        lit_convert += 1
    total += 1

print(f'batch1 total pages: {total}')
print(f'  纯字面转换: {lit_convert}')
print(f'  字面+加引号: {quotes_only}')
print(f'  真白话改写: {real_rewrite}')
