import json
d = json.load(open('_xkb_batch3.json', encoding='utf-8'))
print(f'pages count: {len(d)}')
total_lines = 0
for r in d:
    assert r['page'] in (35, 37, 38, 40, 41, 42, 45, 46, 48), f'unexpected page {r["page"]}'
    assert 'widths' in r and 'text_zh' in r
    assert len(r['text_zh']) > 100
    total_lines += len(r['widths'])
print(f'total lines: {total_lines}')
print(f'all 9 pages OK, all pages have text_zh')
