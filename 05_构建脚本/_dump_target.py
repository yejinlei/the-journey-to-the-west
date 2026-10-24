# -*- coding: utf-8 -*-
"""导出待翻译目标的简短文本，方便人工撰写。"""
import json, sys
from pathlib import Path

d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))

# 用法: python _dump_target.py <edition> [ft1,ft2,...] > out.txt
ed = sys.argv[1]
fts = sys.argv[2].split(',') if len(sys.argv) > 2 else None

rows = []
for l in d['lines']:
    if l.get('edition') != ed: continue
    if fts and l.get('form_type') not in fts: continue
    if l.get('text_zh'): continue  # 已翻译跳过
    rows.append(l)

for l in rows:
    t = (l.get('text') or '').replace('\n', ' ')
    print(f"[{l['page_no']:3d},{l['line_idx']:2d}] {l['form_type']:8s} | {t[:80]}")
