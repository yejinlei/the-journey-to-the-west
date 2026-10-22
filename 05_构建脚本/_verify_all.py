# -*- coding: utf-8 -*-
"""验证三个评点版本完成度"""
import json
from pathlib import Path

data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
lines = data['lines']

PINGS = {'xiyou_yuanzhi', 'baihui_xiangzhu', 'xinke_pingbi'}
FT = {'commentary', 'colophon', 'side', 'inline', 'top', 'bottom', 'title', 'poem', 'verse', 'caption'}

for ed in PINGS:
    subset = [l for l in lines if l.get('edition') == ed and l.get('form_type') in FT]
    total = len(subset)
    done = sum(1 for l in subset if l.get('text_zh'))
    missing = [l for l in subset if not l.get('text_zh')]
    print(f'{ed}: total={total} zh={done} {"✅" if total==done else "❌ 缺 " + str(total-done)}')
    if missing:
        # 按 form_type 分类
        from collections import Counter
        c = Counter(l['form_type'] for l in missing)
        print(f'   缺失分布: {dict(c)}')
        for l in missing[:5]:
            print(f'   p{l["page_no"]},l{l["line_idx"]},{l["form_type"]}: {l["text"][:60]}')
