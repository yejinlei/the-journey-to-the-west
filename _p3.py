import json
d = json.load(open('_xkb_batch1.json','r',encoding='utf-8'))
for e in d:
    t = e['text_zh']
    print(f"p{e['page']}: type={type(t).__name__} len={len(t)} widths_sum={sum(e['widths'])}")
