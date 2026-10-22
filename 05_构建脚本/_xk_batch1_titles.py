# -*- coding: utf-8 -*-
"""xinke_pingbi title 类：卷本名 + 回目（17 行）"""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')
data = json.loads(READ_JSON.read_text(encoding='utf-8'))

BATCH = [
    (4, 0,  "新刻全像批评西游记"),
    (4, 1,  "第八十六回  水母助威征怪物  金公施法灭妖邪"),
    (5, 0,  "木母助威征怪物"),
    (5, 2,  "金公施法灭妖邪"),
    (18, 17, "第八十七回  凤仙郡冒天止雨  孙大圣劝善施霖"),
    (30, 0, "新刻西游评注  卷十九"),
    (30, 5, "第八十八回  禅到玉华施法会  心猿木土授门人"),
    (32, 0, "世说西游证"),
    (32, 12, "世说西游证  卷一"),
    (35, 0, "新刻西游记"),
    (35, 1, "卷十八"),
    (42, 24, "第八十九回"),
    (44, 0, "黄狮精虚设钉耙会"),
    (44, 1, "金木土计闹豹头山"),
    (46, 0, "北平西游评话  卷十八"),
    (46, 4, "北平西游评话  卷十八"),
    (61, 0, "批评西游记"),
]

idx = {(l['page_no'], l['line_idx']): l for l in data['lines']
       if l.get('edition') == 'xinke_pingbi' and l.get('form_type') == 'title'}
for page, line, zh in BATCH:
    key = (page, line)
    assert key in idx, f'not found: {key}'
    idx[key]['text_zh'] = zh

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'写入 {len(BATCH)} 行')
