"""分析 read.json 各 edition 的正文/评点/白话文挂载情况。"""
import json
from collections import Counter, defaultdict

READ = r'f:\src\The-Journey-to-the-West\docs\data\pages\read.json'
d = json.load(open(READ, encoding='utf-8'))

print('=== 顶层键 ===')
print(list(d.keys()))
print('lines 总数:', len(d['lines']))
print('annotations 类型:', type(d.get('annotations')).__name__,
      '长度:', len(d['annotations']) if isinstance(d.get('annotations'), (list, dict)) else '?')

# annotations 样本
ann = d.get('annotations', [])
if isinstance(ann, list) and ann:
    print('annotations[0]:', json.dumps(ann[0], ensure_ascii=False)[:400])
elif isinstance(ann, dict):
    k0 = next(iter(ann)) if ann else None
    if k0:
        print('annotations first key:', k0)
        print('annotations[k0]:', json.dumps(ann[k0], ensure_ascii=False)[:400])

# 各 edition 行数
by_ed = Counter()
by_ed_form = defaultdict(Counter)
by_ed_comment = defaultdict(lambda: Counter())
by_ed_zh = defaultdict(lambda: Counter())
for l in d['lines']:
    e = l['edition']
    by_ed[e] += 1
    by_ed_form[e][l.get('form_type', '?')] += 1
    by_ed_comment[e]['comment' if l.get('is_commentary') else 'main'] += 1
    # 检查白话文相关字段
    has_zh = any(k in l for k in ('text_zh', 'translation', 'translation_zh', 'zh', 'modern_zh'))
    if 'text_zh' in l:
        by_ed_zh[e]['has_text_zh'] += 1

print()
print('=== 各 edition 行数 ===')
for e, c in by_ed.most_common():
    print(f'  {e:22s} {c:6d}')

print()
print('=== 各 edition form_type 分布 ===')
for e, _ in by_ed.most_common():
    print(f'  [{e}]')
    for ft, c in by_ed_form[e].most_common():
        print(f'    {ft:16s} {c:6d}')

print()
print('=== 各 edition 正文/评点分布 ===')
for e, _ in by_ed.most_common():
    c = by_ed_comment[e]
    print(f'  {e:22s} main={c.get("main",0):6d}  comment={c.get("comment",0):6d}')

print()
print('=== text_zh 挂载情况 ===')
for e, c in by_ed.most_common():
    has = by_ed_zh[e].get('has_text_zh', 0)
    print(f'  {e:22s} 有 text_zh: {has:6d} / {by_ed[e]:6d}')

# 查看 gubao 单行完整字段（含 text_zh）
print()
print('=== gubao 单行字段样例 ===')
for l in d['lines']:
    if l['edition'] == 'gubao':
        print('keys:', list(l.keys()))
        print('text_zh 前 80 字:', (l.get('text_zh') or '')[:80])
        break
