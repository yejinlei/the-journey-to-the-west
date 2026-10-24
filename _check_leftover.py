import json
d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())
print('=== xiyou_yuanzhi 剩余 ## 分隔符行 ===')
for l in d['lines']:
    if l.get('edition') == 'xiyou_yuanzhi' and l.get('form_type') == 'main':
        t = l.get('text') or ''
        if len(t) <= 8 or '##' in t:
            z = l.get('text_zh') or ''
            print(f"p{l['page_no']}#{l['line_idx']} text={t!r} zh={z!r}")
print()
print('=== xiyouji_zhuan p2#2 verse ===')
for l in d['lines']:
    if l.get('edition') == 'xiyouji_zhuan' and l['page_no'] == 2 and l['line_idx'] == 2:
        print('text:', l.get('text'))
        print('zh  :', l.get('text_zh'))
