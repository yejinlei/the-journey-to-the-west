# -*- coding: utf-8 -*-
"""xinke_pingbi 剩余 17 行 poem（OCR 打散诗句，独立翻译）"""
import json
from pathlib import Path

READ_JSON = Path('docs/data/pages/read.json')
data = json.loads(READ_JSON.read_text(encoding='utf-8'))

BATCH = {
    # 隐雾山写景诗（连环洞/隐雾山回目，p6）
    (6, 7):  "削峰掩映，怪石嵯峨；奇花瑶草，馨香红杏；碧桃艳丽。",
    (6, 8):  "崖前古树，霜皮溜雨四十围；门外苍松，黛色参天二千尺。",
    (6, 9):  "双双野鹤，常来洞口舞清风；对对山禽，每向枝头啼白昼。",
    (6, 10): "书簇簇黄藤如挂索；行行烟柳似垂金。",
    (6, 11): "方塘积水深穴依山住；多年隐穷龄未变的蛟龙。",
    (6, 12): "吃人的老怪果然不亚神仙境，真是藏风聚气藏身巢。",

    # 玉华县秋景诗（p30，第八十八回玉华施法会）
    (30, 8): "水痕收山骨瘦，红叶纷飞黄花时候；霜晴觉夜长，月白……",

    # 玉华秋景诗续（p32）
    (32, 1): "穿牖透家家烟火，夕阳多处；湖光寒水溜，白蘋香红。",
    (32, 2): "蓼茂橘绿橙黄，柳筛谷秀；荒村雁落碎芦花，野店鸡声。",
    (32, 3): "收菽豆。",

    # 豹头山行路诗（p48，第八十九回）
    (48, 39): "周围山远翠，一脉气连城；峭壁扳青蔓，高崖挂紫荆。",
    (48, 41): "鸟声深树匝花影，洞门迎；不亚桃源洞，堪宜避世情。",

    # 豹头山景诗（p60）
    (60, 0): "峰排突兀岭峻崎岖，深涧下潺湲水激陡崖；前锦绣花……",
    (60, 1): "香回峦重叠，古道湾环；真是鹤来松有伴，果然云去石……",
    (60, 2): "无依。玄猿觅果向晴晖，麋鹿寻花欢日暖；青鸾声渐嚦。",
    (60, 3): "黄鸟语绵蛮；春来桃李争妍，夏至柳槐竞茂，秋到黄花。",
    (60, 4): "布锦冬交白雪飞绵；四时八节好风光，不亚瀛洲仙景。",
}

idx = {(l['page_no'], l['line_idx']): l for l in data['lines']
       if l.get('edition') == 'xinke_pingbi' and l.get('form_type') in ('poem', 'verse')}
for k, zh in BATCH.items():
    assert k in idx, f'not found: {k}'
    idx[k]['text_zh'] = zh

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'写入 {len(BATCH)} 行')
