# -*- coding: utf-8 -*-
"""导出评点待翻译清单 CSV"""
import json, csv
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
PINGS = {'xiyou_yuanzhi', 'baihui_xiangzhu', 'xinke_pingbi'}
FT = {'commentary', 'colophon', 'side', 'inline', 'top', 'bottom', 'title', 'poem', 'caption'}

rows = []
for L in d['lines']:
    if L.get('edition') in PINGS and L.get('form_type') in FT and not L.get('text_zh'):
        rows.append(('lines', L['edition'], L['page_no'], L['line_idx'], L['form_type'], L.get('text','')))

# 排序：先按版本，再按页码
ORDER = ['baihui_xiangzhu', 'xinke_pingbi', 'xiyou_yuanzhi']
rows.sort(key=lambda r: (ORDER.index(r[1]), r[2], r[3]))

with open('05_构建脚本/comments_todo.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['source','edition','page_no','line_idx','form_type','text'])
    w.writerows(rows)

print(f'导出 {len(rows)} 行到 05_构建脚本/comments_todo.csv')
# 分版本统计
import collections
c = collections.Counter(r[1] for r in rows)
for ed, n in c.items(): print(f'  {ed}: {n}')
# 长度分位
lens = [len(r[5]) for r in rows]
lens.sort()
print(f'  len: min={lens[0]} p25={lens[len(lens)//4]} med={lens[len(lens)//2]} p75={lens[3*len(lens)//4]} max={lens[-1]}')
