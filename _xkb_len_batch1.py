import json
d = json.load(open('_xkb_batch1.json', encoding='utf-8'))
for r in d:
    s = sum(r['widths'])
    l = len(r['text_zh'])
    print(f"p{r['page']}: widths_sum={s} text_len={l} diff={l-s}")
