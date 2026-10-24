# -*- coding: utf-8 -*-
"""按 poem 前 3 字在 gubao 中找匹配"""
import json
from pathlib import Path

data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
lines = data['lines']

# 17 个未匹配的 xinke poem
targets = [(6,7),(6,8),(6,9),(6,10),(6,11),(6,12),(30,8),(32,1),(32,2),(32,3),
           (48,39),(48,41),(60,0),(60,1),(60,2),(60,3),(60,4)]
by_key = {(l['page_no'], l['line_idx']): l for l in lines if l.get('edition')=='xinke_pingbi'}

for k in targets:
    l = by_key[k]
    prefix = l['text'].strip()[:6]
    print(f'--- {k}: {l["text"][:40]}')
    # 在 gubao 里找包含此 fragment 的
    for gl in lines:
        if gl.get('edition')=='gubao' and gl.get('text_zh'):
            if prefix[:4] in gl['text'] or gl['text'][:12] in l['text']:
                print(f'    -> gubao p{gl["page_no"]}: {gl["text"][:60]}')
                print(f'         zh: {gl["text_zh"][:80]}')
                break
    print()
