# -*- coding: utf-8 -*-
"""把 xinke_pingbi 的 main 行按 page 合并成段落，dump 给翻译代理看。
输出：_xkb_merged_pX_Y.txt 格式：
## p<page>
LINE_COUNT <n>  # 有多少 main 行
LINE_WIDTHS [w1, w2, ..., wn]  # 每行原始字数
---
<合并后的完整原文段落>
"""
import json
import sys
from pathlib import Path

a, b = int(sys.argv[1]), int(sys.argv[2])
out_path = Path(sys.argv[3])

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
lines = [l for l in d['lines']
         if l.get('edition') == 'xinke_pingbi'
         and l.get('form_type') == 'main'
         and a <= l['page_no'] <= b]

# 按 (page, line_idx) 排序
lines.sort(key=lambda l: (l['page_no'], l['line_idx']))

# 按 page 分组
from collections import defaultdict
by_page = defaultdict(list)
for l in lines:
    by_page[l['page_no']].append(l)

with out_path.open('w', encoding='utf-8') as f:
    for page in sorted(by_page.keys()):
        group = by_page[page]
        texts = [l['text'] for l in group]
        widths = [len(t) for t in texts]
        merged = ''.join(texts)
        f.write(f'## p{page}\n')
        f.write(f'LINE_COUNT {len(texts)}\n')
        f.write(f'LINE_WIDTHS {widths}\n')
        f.write('---\n')
        f.write(merged + '\n')
        f.write('===\n\n')

print(f'paged {len(by_page)}: {a}-{b} -> {out_path}')
print(f'total lines: {len(lines)}')
