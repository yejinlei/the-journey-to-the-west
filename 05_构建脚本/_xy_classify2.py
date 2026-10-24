# -*- coding: utf-8 -*-
import json
from pathlib import Path
data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
xy = [l for l in data['lines'] if l.get('edition')=='xiyou_yuanzhi' and l.get('form_type')=='commentary']
print(f'total: {len(xy)}')
truly_empty = [l for l in xy if not l['text']]
print(f'empty (text==""): {len(truly_empty)}')
whitespace_only = [l for l in xy if l['text'] and not l['text'].strip()]
print(f'whitespace only: {len(whitespace_only)}')
short = [l for l in xy if l['text'].strip() and len(l['text'].strip()) <= 3]
print(f'<=3 chars: {len(short)}')
for l in short[:10]:
    print(f'  p{l["page_no"]},l{l["line_idx"]}: [{l["text"]}]')
