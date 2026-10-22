# -*- coding: utf-8 -*-
"""最终校验：三个评点版本"""
import json
from pathlib import Path
data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))

PINGS = {'xiyou_yuanzhi', 'baihui_xiangzhu', 'xinke_pingbi'}
FT = {'commentary', 'colophon', 'side', 'inline', 'top', 'bottom', 'title', 'poem', 'verse', 'caption'}

grand_total = 0
grand_done = 0
for ed in PINGS:
    subset = [l for l in data['lines'] if l.get('edition') == ed and l.get('form_type') in FT]
    total = len(subset)
    # 空 text 视为不需要翻译（占位符）
    has_text = [l for l in subset if l['text']]
    empty_text = [l for l in subset if not l['text']]
    done = sum(1 for l in has_text if l.get('text_zh'))
    grand_total += total
    grand_done += done
    mark = '✅' if done == len(has_text) else '❌'
    print(f'{ed}: total={total} has_text={len(has_text)} empty={len(empty_text)} zh={done} {mark}')

print(f'\n合计: {grand_done}/{grand_total}')

# gubao
gubao = [l for l in data['lines'] if l.get('edition')=='gubao']
gubao_done = sum(1 for l in gubao if l.get('text_zh'))
print(f'gubao: total={len(gubao)} zh={gubao_done}')
