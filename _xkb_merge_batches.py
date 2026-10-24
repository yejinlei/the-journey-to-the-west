# -*- coding: utf-8 -*-
"""验证 5 个 xkb batch JSON 并与 _xkb_merged.txt 期望对齐"""
import json
from pathlib import Path

BATCHES = ['_xkb_batch1.json', '_xkb_batch2.json', '_xkb_batch3.json', '_xkb_batch4.json', '_xkb_batch5.json']
merged = Path('_xkb_merged.txt').read_text(encoding='utf-8')

# 解析 merged.txt
import re
expected = {}
page_re = re.compile(r'^## p(\d+)$', re.M)
count_re = re.compile(r'^LINE_COUNT (\d+)$', re.M)
widths_re = re.compile(r'^LINE_WIDTHS \[([^\]]+)\]$', re.M)
chunks = page_re.split(merged)
# chunks: ['', 'page1', 'content1', 'page2', 'content2', ...]
for i in range(1, len(chunks), 2):
    page = int(chunks[i])
    content = chunks[i+1]
    m_c = count_re.search(content)
    m_w = widths_re.search(content)
    n = int(m_c.group(1))
    widths = [int(x) for x in m_w.group(1).split(',')]
    expected[page] = (n, widths)

print(f'期望 page 数: {len(expected)}')
print(f'期望总行数: {sum(v[0] for v in expected.values())}')

# 加载 5 个 batch
all_pages = {}
total_lines = 0
for bf in BATCHES:
    d = json.loads(Path(bf).read_text(encoding='utf-8'))
    print(f'\n{bf}: {len(d)} pages')
    for entry in d:
        p = entry['page']
        w = entry['widths']
        zh = entry['text_zh']
        all_pages[p] = (w, zh)
        total_lines += len(w)
        exp_n, exp_w = expected.get(p, (None, None))
        status = 'OK'
        if exp_n is None:
            status = 'UNEXPECTED PAGE'
        elif len(w) != exp_n:
            status = f'LINE_COUNT MISMATCH exp={exp_n} got={len(w)}'
        elif w != exp_w:
            status = f'WIDTHS MISMATCH'
        diff = len(zh) - sum(w)
        print(f'  p{p}: nlines={len(w)} sum_w={sum(w)} len_zh={len(zh)} diff={diff:+d} {status}')

print(f'\n已收到 page 数: {len(all_pages)}')
print(f'已收到总行数: {total_lines}')
missing = sorted(set(expected.keys()) - set(all_pages.keys()))
print(f'缺失 page: {missing}')
