import json
d = json.loads(open('_xyzhuan_trunc.json', 'r', encoding='utf-8').read())
print(f'共 {len(d)} 行')
for x in d:
    t = x['text']
    z = x['old_zh']
    print(f"p{x['page_no']}#{x['line_idx']}: 原文{len(t)}字, 旧白话{len(z)}字")
