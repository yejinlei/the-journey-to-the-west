# -*- coding: utf-8 -*-
"""扫描 gubao 所有实质改写行，按差异字符数排序"""
import json
from pathlib import Path
from opencc import OpenCC
from difflib import SequenceMatcher

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
cc = OpenCC('t2s')

lines = [l for l in d['lines']
         if l.get('edition') == 'gubao'
         and l.get('form_type') in ('main', 'verse', 'title', 'poem')
         and l.get('text_zh')]

# 分类
buckets = {
    'literal_only': [],   # text_zh == OpenCC(text)
    'tiny_diff': [],      # 1-3 字差异（可能是同义替换）
    'medium_diff': [],    # 4-15 字差异
    'big_diff': [],       # >15 字差异（大概率有改动语义）
}

for l in lines:
    oc = cc.convert(l['text'])
    if l['text_zh'] == oc:
        buckets['literal_only'].append(l)
        continue
    sm = SequenceMatcher(None, oc, l['text_zh'])
    ops = sm.get_opcodes()
    n_ops = sum(1 for tag, i1, i2, j1, j2 in ops if tag != 'equal')
    n_changed = sum(max(i2-i1, j2-j1) for tag, i1, i2, j1, j2 in ops if tag != 'equal')
    l['_n_ops'] = n_ops
    l['_n_changed'] = n_changed
    if n_changed <= 3:
        buckets['tiny_diff'].append(l)
    elif n_changed <= 15:
        buckets['medium_diff'].append(l)
    else:
        buckets['big_diff'].append(l)

out = []
out.append(f'gubao total lines with text_zh: {len(lines)}')
for k, v in buckets.items():
    out.append(f'  {k}: {len(v)}')

out.append('\n--- big_diff 样本（按差异从大到小） ---')
big = sorted(buckets['big_diff'], key=lambda x: -x['_n_changed'])[:20]
for l in big:
    out.append(f'')
    out.append(f'--- p{l["page_no"]}i{l["line_idx"]} [{l["form_type"]}] ops={l["_n_ops"]} changed={l["_n_changed"]}/{len(l["text"])} ---')
    out.append(f'SRC: {l["text"][:200]}')
    out.append(f'OC : {cc.convert(l["text"])[:200]}')
    out.append(f'ZH : {l["text_zh"][:200]}')

Path('_gubao_scan.txt').write_text('\n'.join(out), encoding='utf-8')
print(f'OK. big_diff={len(buckets["big_diff"])}, medium={len(buckets["medium_diff"])}, tiny={len(buckets["tiny_diff"])}, literal={len(buckets["literal_only"])}')
