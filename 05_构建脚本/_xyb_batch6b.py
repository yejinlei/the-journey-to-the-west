# -*- coding: utf-8 -*-
"""xiyou_bu batch6b: page 8 lines 11-12 (补漏)"""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')

BATCH = {
(8,11): "鼓声才罢,行者便叫:'放了秦桧绑子,细细问他!'一千个无职雄风鬼慌忙解下绳来,把秦桧一揪揪下石皮,踢了几脚。秦桧伏在地上,不敢做声。行者便叫:'秦丞相请了!'",
(8,12): "(写行者扮威仪处,一一绝倒。)",
}

data = json.loads(READ_JSON.read_text(encoding='utf-8'))
idx = {}
for l in data['lines']:
    if l.get('edition') != 'xiyou_bu':
        continue
    if l.get('form_type') not in ('main', 'verse'):
        continue
    idx[(l['page_no'], l['line_idx'])] = l

missing = [k for k in BATCH if k not in idx]
assert not missing, f'not found keys: {missing}'

for k, zh in BATCH.items():
    idx[k]['text_zh'] = zh

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'写入 {len(BATCH)} 行')
