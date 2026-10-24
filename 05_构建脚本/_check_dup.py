# -*- coding: utf-8 -*-
"""检查 lines vs annotations 是否重复"""
import json
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))

# 检查 xinke_pingbi 中 lines 和 annotations 是否有交集
lines_keys = set()
lines_by_ed = {'xinke_pingbi': []}
for L in d['lines']:
    if L.get('edition') == 'xinke_pingbi' and L.get('form_type') in {'colophon','side','inline','top','bottom','caption'}:
        key = (L['page_no'], L['line_idx'], L['form_type'], L.get('text','')[:40])
        lines_keys.add(key)
        lines_by_ed['xinke_pingbi'].append(L)

ann_keys = set()
ann = [L for L in d['annotations'] if L.get('edition') == 'xinke_pingbi']
for L in ann:
    key = (L['page_no'], L['line_idx'], L.get('form_type',''), L.get('text','')[:40])
    ann_keys.add(key)

print(f'lines（朱批 5 类）: {len(lines_by_ed["xinke_pingbi"])}')
print(f'annotations: {len(ann)}')
print(f'交集: {len(lines_keys & ann_keys)}')
# 只在一个不在另一个
only_lines = lines_keys - ann_keys
only_ann = ann_keys - lines_keys
print(f'只在线: {len(only_lines)}  只在注: {len(only_ann)}')

# 样本对比
print('\n--- lines 朱批样本 ---')
for L in lines_by_ed['xinke_pingbi'][:5]:
    print(f"  p{L['page_no']} L{L['line_idx']} [{L['form_type']}]: {L.get('text','')[:60]}")
print('\n--- annotations 样本 ---')
for L in ann[:5]:
    print(f"  p{L['page_no']} L{L['line_idx']} [{L.get('form_type','')}]: {L.get('text','')[:60]}")
