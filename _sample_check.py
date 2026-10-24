# -*- coding: utf-8 -*-
"""抽样检查 text_zh 改写质量"""
import json
import random
from pathlib import Path
from opencc import OpenCC

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
cc = OpenCC('t2s')

TARGETS = ['baihui_xiangzhu', 'xiyouji_zhuan', 'xinke_pingbi']

out = []
random.seed(42)
for ed in TARGETS:
    lines = [l for l in d['lines']
             if l.get('edition') == ed
             and l.get('form_type') in ('main', 'verse', 'title', 'poem', 'commentary', 'colophon')
             and l.get('text_zh')]
    if not lines:
        continue

    has_diff = []
    for l in lines:
        oc = cc.convert(l['text'])
        if l['text_zh'] != oc:
            diffs = sum(1 for a, b in zip(oc, l['text_zh']) if a != b)
            max_len = max(len(oc), len(l['text_zh']))
            ratio = diffs / max_len if max_len else 0
            if ratio > 0.05:
                has_diff.append((l, diffs, ratio))

    out.append(f'===== {ed} =====')
    out.append(f'total_with_text_zh={len(lines)}, real_rewrites_gt5pct={len(has_diff)}')

    sample = random.sample(has_diff, min(5, len(has_diff)))
    for l, diffs, ratio in sample:
        out.append('')
        out.append(f'--- p{l["page_no"]}i{l["line_idx"]} [{l["form_type"]}] diff={diffs}/{len(l["text"])} ({ratio*100:.1f}%) ---')
        out.append(f'SRC: {l["text"][:300]}')
        out.append(f'ZH : {l["text_zh"][:300]}')

Path('_sample_check.txt').write_text('\n'.join(out), encoding='utf-8')
print('OK')
