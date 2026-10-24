"""修复 gubao 每章首页 line_idx=0 的 JSON 元数据污染

原文形如：
  「盡三三行滿道歸根 | author = 吳承恩 | previous = ... | next = ... | notes =  }}」
应清理为：
  「盡三三行滿道歸根」

规则：若 text 中含 ` | ` 且后半段出现 `author/previous/next/notes =` 之一，
则只保留第一段（标题本身）。对 text 和 text_zh 同步处理。
"""
import json, re
from pathlib import Path

SRC = Path('docs/data/pages/read.json')
d = json.loads(SRC.read_text(encoding='utf-8'))

META_KEYS = ('author', 'previous', 'next', 'notes', 'title', 'chapter')
SPLIT = ' | '
RE_META = re.compile(r'\b(' + '|'.join(META_KEYS) + r')\s*=')

fixed = 0
samples_before = []
samples_after = []

for l in d['lines']:
    if l.get('edition') != 'gubao':
        continue
    for fld in ('text', 'text_zh'):
        v = l.get(fld) or ''
        if SPLIT not in v:
            continue
        first, rest = v.split(SPLIT, 1)
        if RE_META.search(rest):
            if len(samples_before) < 6 and fld == 'text':
                samples_before.append((l['page_no'], l['line_idx'], v))
            new = first.strip()
            l[fld] = new
            if fld == 'text_zh':
                fixed += 1
                if len(samples_after) < 6:
                    samples_after.append((l['page_no'], l['line_idx'], new))

print(f'清理行数（按 text_zh 计）: {fixed}')
print('\n--- 修复前样本 ---')
for p, i, v in samples_before:
    print(f'  p{p}#{i}: {v[:120]}')
print('\n--- 修复后样本 ---')
for p, i, v in samples_after:
    print(f'  p{p}#{i}: {v}')

# 检查修复后是否还有残留
residual = 0
for l in d['lines']:
    if l.get('edition') != 'gubao':
        continue
    for fld in ('text', 'text_zh'):
        v = l.get(fld) or ''
        if 'notes' in v or '}}' in v or 'author =' in v or 'previous =' in v or 'next =' in v:
            residual += 1
            if residual <= 5:
                print(f'  [残留] p{l["page_no"]}#{l["line_idx"]} {fld}: {v[:120]}')
print(f'\n修复后残留: {residual}')

if residual == 0:
    SRC.write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('\n已写回 docs/data/pages/read.json')
