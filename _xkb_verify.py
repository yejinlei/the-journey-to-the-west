import json
d = json.load(open('_xkb_batch3.json', encoding='utf-8'))
print(f'pages: {len(d)}')
print(f'total lines: {sum(len(r["widths"]) for r in d)}')
for r in d:
    print(f"p{r['page']}: lines={len(r['widths'])} widths_sum={sum(r['widths'])} text_len={len(r['text_zh'])}")
