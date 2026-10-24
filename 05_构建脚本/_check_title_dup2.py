# -*- coding: utf-8 -*-
"""排查 gubao title 情况"""
import json
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))

gb_titles = [L for L in d['lines'] if L.get('edition')=='gubao' and L.get('form_type')=='title']
print(f'gubao titles: {len(gb_titles)}')
with_zh = [L for L in gb_titles if L.get('text_zh')]
print(f'  with text_zh: {len(with_zh)}')
for L in with_zh[:3]:
    print(f"  p{L['page_no']} L{L['line_idx']}: text={L['text'][:40]}")
    print(f"    zh={L['text_zh'][:60]}")

# 全表 title form_type 分布
import collections
c = collections.Counter(L.get('form_type') for L in d['lines'] if L.get('edition')=='gubao')
print('\ngubao form_type 分布:', dict(c))

# baihui title 样本对比 gubao main 中的回目行
bh_titles_text = set(L['text'] for L in d['lines'] if L.get('edition')=='baihui_xiangzhu' and L.get('form_type')=='title')
gb_all_text_zh = {L['text']: L['text_zh'] for L in d['lines'] if L.get('edition')=='gubao' and L.get('text_zh')}
matched = 0
for t in bh_titles_text:
    if t in gb_all_text_zh:
        matched += 1
print(f'\nbaihui title 在 gubao 任何有 zh 的 text 中找到: {matched}/{len(bh_titles_text)}')
# 尝试去掉空格
gb_text_set = set(L['text'] for L in d['lines'] if L.get('edition')=='gubao')
print(f'baihui title 在 gubao text 中（不论 zh）: {sum(1 for t in bh_titles_text if t in gb_text_set)}')

# 检查是否有繁简差异
print('\n示例对比:')
for t in list(bh_titles_text)[:3]:
    print(f'  baihui: {t}')
    # 找 gubao 中相似
    for L in d['lines']:
        if L.get('edition')=='gubao' and L.get('text','').replace(' ','') == t.replace(' ','') and L.get('text_zh'):
            print(f'    -> gubao: {L["text"]}')
            print(f'       zh={L["text_zh"]}')
            break
    else:
        print(f'    -> (gubao 中未找到匹配)')
