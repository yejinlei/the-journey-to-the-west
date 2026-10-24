# -*- coding: utf-8 -*-
"""检查 baihui_xiangzhu title 是否与 gubao 重复"""
import json
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))

# baihui title
bh_titles = [(L['page_no'], L['line_idx'], L['text']) for L in d['lines']
             if L.get('edition')=='baihui_xiangzhu' and L.get('form_type')=='title' and not L.get('text_zh')]
print(f'baihui_xiangzhu titles: {len(bh_titles)}')

# gubao title 已有 text_zh
gb_titles = {(L['page_no'], L['text']) for L in d['lines']
             if L.get('edition')=='gubao' and L.get('form_type')=='title' and L.get('text_zh')}
print(f'gubao titles with text_zh: {len.gb_titles} ' if False else f'gubao titles with text_zh: {len(gb_titles)}')

# 匹配（页码可能不同，用 text 匹配）
matched = sum(1 for _,_,t in bh_titles if (0,t) in [(p,t) for p,t in gb_titles])
# 实际用文本匹配
gb_text_set = {t for _,t in gb_titles}
matched = sum(1 for _,_,t in bh_titles if t in gb_text_set)
print(f'baihui title 在 gubao title 中能找到: {matched}')

# 检查 baihui_xiangzhu title 是否已经在 gubao 有对应 text_zh（按文本）
gb_text_to_zh = {}
for L in d['lines']:
    if L.get('edition')=='gubao' and L.get('form_type')=='title' and L.get('text_zh'):
        gb_text_to_zh[L['text']] = L['text_zh']

copyable = 0
for _,_,t in bh_titles:
    if t in gb_text_to_zh:
        copyable += 1
print(f'可直接从 gubao 复制 text_zh: {copyable}')

# 看看剩下的差什么
diffs = [t for _,_,t in bh_titles if t not in gb_text_to_zh]
print(f'差集（baihui 独有 title）: {len(diffs)}')
for t in diffs[:10]:
    print(f'  {t}')
