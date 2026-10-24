"""最后 2 项修复：xiyou_yuanzhi 7 行 ## 分隔符 + xiyouji_zhuan p2#2 verse 补全"""
import json, opencc
from pathlib import Path

T2S = opencc.OpenCC('t2s')
SRC = Path('docs/data/pages/read.json')
d = json.loads(SRC.read_text(encoding='utf-8'))

# 1) xiyou_yuanzhi 7 个 ## 分隔符行 → 规范化
SEP_COUNT = 0
for l in d['lines']:
    if l.get('edition') == 'xiyou_yuanzhi' and l.get('form_type') == 'main':
        t = l.get('text') or ''
        if len(t) <= 8 and '##' in t:
            l['text'] = '##'
            l['text_zh'] = '##'
            SEP_COUNT += 1
print(f'xiyou_yuanzhi ## 分隔符行规范化: {SEP_COUNT}')

# 2) xiyouji_zhuan p2#2 verse 完整 OpenCC 转（保留原文含括注）
VERSE_TEXT = (
    "顯密圓通真妙決，惜修性命無他說。\n"
    "都來總是精氣神，謹固牢藏休漏泄。\n"
    "休漏泄，體中藏，汝受吾傳道自具。\n"
    "口訣記來多有益，屏除邪欲得清涼。\n"
    "得清涼（原缺此三字），光皎潔，好向丹台賞明月。\n"
    "月藏玉兔日藏烏，自有鬼蛇相盤結。\n"
    "相盤結，性命堅，卻能火裡種金蓮。\n"
    "攢簇五行顛倒用，功完隨作佛和仙。"
)
count = 0
for l in d['lines']:
    if l.get('edition') == 'xiyouji_zhuan' and l['page_no'] == 2 and l['line_idx'] == 2:
        l['text_zh'] = T2S.convert(VERSE_TEXT)
        count += 1
        print(f"xiyouji_zhuan p2#2 verse 修复: {len(l['text_zh'])} 字")
print(f'verse 处理行数: {count}')

SRC.write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print('已写回 read.json')
