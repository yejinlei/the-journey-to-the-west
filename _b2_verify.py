import json
d = json.load(open('_xkb_batch2.json', 'r', encoding='utf-8'))
print(f'pages: {len(d)}')
total_lines = 0
for x in d:
    print(f'p{x["page"]}: nlines_expected={len(x["widths"])}, len={len(x["text_zh"])}, sum_widths={sum(x["widths"])}')
    total_lines += len(x['widths'])
print(f'total lines: {total_lines}')
