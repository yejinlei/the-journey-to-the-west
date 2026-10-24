# -*- coding: utf-8 -*-
"""跳过 xiyou_yuanzhi 101 行 OCR 噪声 commentary，text_zh 原样保留"""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')
d = json.loads(READ_JSON.read_text(encoding='utf-8'))

n = 0
for l in d['lines']:
    if l.get('edition') != 'xiyou_yuanzhi':
        continue
    if l.get('form_type') != 'commentary':
        continue
    if l.get('text_zh'):
        continue
    t = l.get('text', '')
    # 仅处理 OCR 噪声（长度极短、无非 ASCII 字符）
    if len(t) <= 10:
        l['text_zh'] = t  # 原样保留
        n += 1
    else:
        print(f'跳过（非噪声，需人工翻译）: p{l["page_no"]}i{l["line_idx"]} len={len(t)} {t[:80]!r}')

READ_JSON.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'标记跳过 {n} 行 OCR 噪声')
