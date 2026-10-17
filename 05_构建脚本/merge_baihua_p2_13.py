# -*- coding: utf-8 -*-
# 合并 baihua_data/gubao_p{2..13}.json 译文，注入 docs/data/pages/read.json 的 text_zh
import json, glob, os, sys

BASE = r'f:\src\The-Journey-to-the-West'
READ = os.path.join(BASE, 'docs', 'data', 'pages', 'read.json')
DATA = os.path.join(BASE, '05_构建脚本', 'baihua_data')

# 1) 载入全部译文 JSON 并校验
trans = {}  # (page, line_idx) -> text
for fp in sorted(glob.glob(os.path.join(DATA, 'gubao_p*.json'))):
    with open(fp, encoding='utf-8') as f:
        d = json.load(f)
    page = d['page']
    assert 2 <= page <= 13, fp
    for k, v in d['translations'].items():
        assert '"' not in v, ('ASCII quote in', fp, k)
        trans[(page, int(k))] = v
    print('loaded', os.path.basename(fp), 'page', page, 'lines', len(d['translations']))

print('total translation lines:', len(trans))

# 2) 注入 read.json
with open(READ, encoding='utf-8') as f:
    d = json.load(f)

n_inject = 0
n_zh_total = 0
for l in d['lines']:
    if l.get('edition') == 'gubao':
        key = (l['page_no'], l['line_idx'])
        if key in trans:
            l['text_zh'] = trans[key]
            n_inject += 1
        if 'text_zh' in l:
            n_zh_total += 1

with open(READ, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, separators=(',', ':'))

print('injected this batch:', n_inject, '/ expected', len(trans))
print('total text_zh lines now:', n_zh_total)
