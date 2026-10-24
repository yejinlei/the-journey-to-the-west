# -*- coding: utf-8 -*-
"""用 OpenCC 检查 text_zh 是否还是繁体"""
import json
import opencc
_T2S = opencc.OpenCC('t2s')

for bf in ['_xkb_batch1.json', '_xkb_batch2.json', '_xkb_batch3.json', '_xkb_batch4.json', '_xkb_batch5.json']:
    entries = json.load(open(bf, 'r', encoding='utf-8'))
    print(f'\n=== {bf} ===')
    for e in entries:
        zh = e['text_zh']
        simp = _T2S.convert(zh)
        # 找不同的位置
        diffs = [(i, a, b) for i,(a,b) in enumerate(zip(zh, simp)) if a != b]
        # 只关注繁体→简体差异（前几个字符）
        sample = ''.join(a for _,a,_ in diffs[:15])
        n_diff = len(diffs)
        ratio = n_diff / max(len(zh), 1)
        flag = '仍有繁' if ratio > 0.02 else 'OK'
        print(f'  p{e["page"]}: 差异{ratio:.1%} ({n_diff}处) [{sample}] {flag}')
