# -*- coding: utf-8 -*-
"""补齐 xinke_pingbi 遗漏的 23 行"""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')
data = json.loads(READ_JSON.read_text(encoding='utf-8'))

BATCH = {
    (4, 4):   "批评西游记",
    (4, 5):   "批评西游记",
    (18, 22): "全像西游记",
    (23, 22): "卷十八",
    (24, 22): "凡例",
    (24, 23): "卷十八",
    (26, 22): "批评西游记",
    (26, 23): "卷十八",
    (28, 22): "批评西游记",
    (28, 23): "卷十八",
    (31, 1):  "禅到玉华施法会",
    (31, 2):  "心猿木土授门人",
    (35, 2):  "批评西游记",
    (37, 22): "卷十八",
    (37, 23): "三十六",
    (42, 22): "总批：既要做他们徒弟，只合学空、学能、学净，却去学棒、学",
    (42, 23): "钺、学杖，所以今之学者，只能得师门之糟粕而已。",
    (42, 26): "四十",
    (44, 2):  "卷十八  四二",
    (50, 0):  "批言",
    (63, 22): "古本西游证记",
    (63, 23): "六十一",
    (65, 22): "卷十八",
}

idx = {(l['page_no'], l['line_idx']): l for l in data['lines']
       if l.get('edition') == 'xinke_pingbi'}
for k, zh in BATCH.items():
    if k in idx and not idx[k].get('text_zh'):
        idx[k]['text_zh'] = zh

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'处理 {len(BATCH)} 条')
