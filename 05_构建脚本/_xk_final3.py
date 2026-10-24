# -*- coding: utf-8 -*-
import json
from pathlib import Path
READ_JSON = Path('docs/data/pages/read.json')
data = json.loads(READ_JSON.read_text(encoding='utf-8'))

BATCH = {
    (37, 0):  "批词西游词",
    (40, 22): "便放出去，全无孔便；易光生古。",
    (42, 0):  "四十",
}
idx = {(l['page_no'], l['line_idx']): l for l in data['lines']
       if l.get('edition') == 'xinke_pingbi'}
for k, zh in BATCH.items():
    if k in idx:
        idx[k]['text_zh'] = zh

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'完成 {len(BATCH)}')
