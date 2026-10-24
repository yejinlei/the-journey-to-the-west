# -*- coding: utf-8 -*-
import json
from pathlib import Path
data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
xy = [l for l in data['lines'] if l.get('edition')=='xiyou_yuanzhi' and l.get('form_type')=='commentary']
empty = [l for l in xy if not l['text'].strip()]
has = [l for l in xy if l['text'].strip()]
print(f'empty: {len(empty)}, has_text: {len(has)}')
# 打印前 30 个有内容的
for l in has[:30]:
    print(f'p{l["page_no"]},l{l["line_idx"]}: {l["text"][:80]}')
