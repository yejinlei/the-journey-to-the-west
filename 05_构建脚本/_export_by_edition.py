# -*- coding: utf-8 -*-
"""按版本+页码导出评点清单，方便分批翻译"""
import json, csv
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))

def dump(edition, name):
    FT = {'commentary', 'colophon', 'side', 'inline', 'top', 'bottom', 'title', 'poem', 'caption'}
    rows = [L for L in d['lines']
            if L.get('edition')==edition and L.get('form_type') in FT and not L.get('text_zh')]
    rows.sort(key=lambda r: (r['page_no'], r['line_idx'], r['form_type']))
    path = f'05_构建脚本/{name}.csv'
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['page_no','line_idx','form_type','text'])
        for L in rows:
            w.writerow([L['page_no'], L['line_idx'], L['form_type'], L.get('text','')])
    print(f'{name}.csv: {len(rows)} rows')
    return rows

dump('baihui_xiangzhu', 'bh_xiangzhu')
dump('xinke_pingbi', 'xinke_pingbi')
dump('xiyou_yuanzhi', 'xiyou_yuanzhi')
