# -*- coding: utf-8 -*-
"""把 5 个 _xkb_batch*.json 合并写入 read.json。
策略：
- 按 page 加载 widths + text_zh
- 对每个 page 查 read.json 的 main 行，按顺序切分 text_zh 到各行
- 若 len(text_zh) != sum(widths)，按比例调整（每行按 widths[i] * ratio 分配）
- 尽量让每行长度 == widths[i]
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
READ_JSON = BASE / 'docs/data/pages/read.json'

BATCHES = ['_xkb_batch1.json', '_xkb_batch2.json', '_xkb_batch3.json', '_xkb_batch4.json', '_xkb_batch5.json']


def split_by_widths(text, widths):
    """把 text 按 widths 列表切分为 len(widths) 段。
    总长 len(text) 与 sum(widths) 不一致时，按比例分配并微调。
    """
    n = len(widths)
    L = len(text)
    W = sum(widths)
    if n == 0:
        return []
    if L == 0:
        return [''] * n
    # 计算每段的浮点长度
    targets = [widths[i] * L / W for i in range(n)]
    # 用 round 分配整数长度，然后调整尾差
    allocated = [round(t) for t in targets]
    diff = L - sum(allocated)
    # 把 diff 分摊到最长的几段
    if diff != 0:
        order = sorted(range(n), key=lambda i: -targets[i])
        idx = 0
        while diff != 0 and order:
            i = order[idx % len(order)]
            if diff > 0 and i < n:
                allocated[i] += 1
                diff -= 1
            elif diff < 0 and allocated[i] > 1:
                allocated[i] -= 1
                diff += 1
            idx += 1
    # 切分
    parts = []
    pos = 0
    for a in allocated:
        parts.append(text[pos:pos+a])
        pos += a
    return parts


data = json.loads(READ_JSON.read_text(encoding='utf-8'))

# 按 page 分组 main 行
main_by_page = {}
for l in data['lines']:
    if l.get('edition') == 'xinke_pingbi' and l.get('form_type') == 'main':
        main_by_page.setdefault(l['page_no'], []).append(l)
for p in main_by_page:
    main_by_page[p].sort(key=lambda l: l['line_idx'])

# 加载 5 个 batch
translations = {}
for bf in BATCHES:
    entries = json.loads((BASE / bf).read_text(encoding='utf-8'))
    for e in entries:
        translations[e['page']] = (e['widths'], e['text_zh'])

print(f'page 数: main={len(main_by_page)}, translations={len(translations)}')

written = 0
mismatch = 0
for page, (widths, text_zh) in sorted(translations.items()):
    rows = main_by_page.get(page)
    if rows is None:
        print(f'WARN: p{page} 在 read.json 中找不到 main 行')
        continue
    parts = split_by_widths(text_zh, widths)
    if len(parts) != len(rows):
        print(f'WARN: p{page} 切分得 {len(parts)} 段但读 json 有 {len(rows)} 行')
        mismatch += 1
        continue
    for i, (row, part) in enumerate(zip(rows, parts)):
        row['text_zh'] = part
        if len(part) != widths[i]:
            mismatch += 1
            if mismatch < 20:
                print(f'WARN p{page}[{row["line_idx"]}]: len={len(part)} vs width={widths[i]}')
        written += 1

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'写入 {written} 行, 长度不匹配 {mismatch} 处')
