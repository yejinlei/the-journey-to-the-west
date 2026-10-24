# -*- coding: utf-8 -*-
"""xinke_pingbi batch 21: page 69."""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')

BATCH = {
    (69, 1): "顿脱群思乃此回之本意也",
    (69, 2): "急着眼急着眼○六狮",
    (69, 3): "砍头黄狮剥皮快则快矣安得把世上许多误人子",
    (69, 4): "弟的庸师一并食肉寝皮更为快也",
    (69, 5): "风快焚香入殿敬门前",
    (69, 6): "不果",
    (69, 7): "文笔",
    (69, 8): "只",
    (69, 9): "内",
    (69, 10): "三人",
    (69, 11): "命",
    (69, 12): "子",
    (69, 13): "人",
    (69, 14): "金",
    (69, 15): "不",
    (69, 16): "受",
    (69, 17): "奈",
    (69, 18): "回",
    (69, 19): "好",
    (69, 20): "书",
    (69, 21): "大",
    (69, 22): "那",
    (69, 23): "好",
    (69, 24): "想",
}

data = json.loads(READ_JSON.read_text(encoding='utf-8'))
idx = {}
for l in data['lines']:
    if l.get('edition') != 'xinke_pingbi':
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
