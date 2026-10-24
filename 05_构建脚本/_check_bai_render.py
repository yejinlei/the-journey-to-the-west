import json
from collections import Counter

d = json.load(open(r'docs/data/pages/read.json', encoding='utf-8'))
lines = d.get('lines', [])
chapters = d.get('chapters', [])

# gubao 章节
gubao_ch = sorted([c for c in chapters if c.get('edition') == 'gubao'], key=lambda x: x.get('first_page', 0))
print('gubao 回章节数:', len(gubao_ch))

# 按 edition 统计 text_zh 覆盖
for ed in sorted(set(l.get('edition') for l in lines)):
    sub = [l for l in lines if l.get('edition') == ed]
    main = [l for l in sub if l.get('form_type') == 'main']
    has = [l for l in sub if l.get('text_zh')]
    print(f'  {ed}: total={len(sub)} main={len(main)} with_zh={len(has)}')

# gubao 中每回覆盖率
print('\ngubao 每回 text_zh 覆盖:')
for c in gubao_ch:
    fp = c['first_page']
    lp = c.get('last_page') or fp
    sub = [l for l in lines if l.get('edition') == 'gubao' and fp <= l.get('page_no', 0) <= lp]
    main = [l for l in sub if l.get('form_type') == 'main']
    has = [l for l in main if l.get('text_zh')]
    pct = len(has) / len(main) * 100 if main else 0
    if pct < 100:
        print(f'  {c.get("chapter_label")}: page={fp} main={len(main)} has_zh={len(has)} ({pct:.0f}%)')
