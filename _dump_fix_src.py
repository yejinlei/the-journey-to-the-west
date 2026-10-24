"""导出待重翻译原文"""
import json
d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())

tasks = {
    'A_xiyouji_zhuan_p1_0': ('xiyouji_zhuan', 1, 0),
    'B_xiyou_yuanzhi_p1_2': ('xiyou_yuanzhi', 1, 2),
    'B_xiyou_yuanzhi_p1_5': ('xiyou_yuanzhi', 1, 5),
    'B_xiyou_yuanzhi_p1_8': ('xiyou_yuanzhi', 1, 8),
    'B_xiyou_yuanzhi_p1_11': ('xiyou_yuanzhi', 1, 11),
    'B_xiyou_yuanzhi_p1_14': ('xiyou_yuanzhi', 1, 14),
    'B_xiyou_yuanzhi_p1_20': ('xiyou_yuanzhi', 1, 20),
    'C_gubao_p93_0': ('gubao', 93, 0),
}
for name, (ed, pg, li) in tasks.items():
    l = next(x for x in d['lines'] if x.get('edition')==ed and x['page_no']==pg and x['line_idx']==li)
    print(f'===== {name} ({ed}/{l.get("form_type")}) =====')
    print('原文:')
    print(l.get('text',''))
    print('当前白话:')
    print(l.get('text_zh',''))
    print()
