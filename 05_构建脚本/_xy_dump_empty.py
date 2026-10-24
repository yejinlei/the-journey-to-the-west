# -*- coding: utf-8 -*-
import json
from pathlib import Path
data = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
xy = [l for l in data['lines'] if l.get('edition')=='xiyou_yuanzhi' and l.get('form_type')=='commentary']
empty_rows = [l for l in xy if l['text'] == '']
print(f'p*_l0 empty count: {len(empty_rows)}')
print('first 5:', [(l['page_no'], l['line_idx']) for l in empty_rows[:5]])
print('last 5:', [(l['page_no'], l['line_idx']) for l in empty_rows[-5:]])
# non-empty
non_empty = [l for l in xy if l['text'] != '']
print(f'non-empty: {len(non_empty)}')
