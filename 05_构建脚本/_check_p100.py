"""检查最后一回 p99 白话 vs 原文"""
import json
d = json.load(open(r'docs/data/pages/read.json', encoding='utf-8'))
chapters = d.get('chapters', [])
lines = d.get('lines', [])

gubao_ch = [c for c in chapters if c.get('edition') == 'gubao']
gubao_ch.sort(key=lambda x: x.get('first_page', 0))
last = gubao_ch[-1]
print(f'最后一回: {last.get("chapter_label")}  page {last.get("first_page")}-{last.get("last_page")}')

fp = last['first_page']
lp = last.get('last_page') or fp
sub = [l for l in lines if l.get('edition') == 'gubao' and fp <= l.get('page_no', 0) <= lp]

print(f'\n行数: {len(sub)}')
print(f'{"L":>4} {"form":<10} {"同?":<6} {"text":<40} | {"text_zh":<40}')
print('-' * 130)
for l in sub[:50]:
    t = (l.get('text') or '').replace('\n',' ')[:38]
    z = (l.get('text_zh') or '').replace('\n',' ')[:38]
    if (l.get('text') or '') == (l.get('text_zh') or ''):
        mark = 'SAME'
    elif not z:
        mark = 'no_zh'
    else:
        mark = ''
    print(f'{l.get("line_idx",0):>4} {l.get("form_type",""):<10} {mark:<6} {t:<40} | {z:<40}')

total = len(sub)
has_zh = len([l for l in sub if l.get('text_zh')])
same = len([l for l in sub if (l.get('text') or '') == (l.get('text_zh') or '')])
no_zh = total - has_zh
print(f'\n总={total} 含zh={has_zh} 完全相同={same} 无zh={no_zh}')

# 检查 form_type 分布
from collections import Counter
print('\nform_type 分布:', Counter(l.get('form_type') for l in sub))
