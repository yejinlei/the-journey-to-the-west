import json
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
for l in d['lines']:
    if l.get('edition') != 'baihui_xiangzhu':
        continue
    if l.get('form_type') not in ('main', 'verse'):
        continue
    if 55 <= l['page_no'] <= 60:
        t = l.get('text_zh') or ''
        print(f"[{l['page_no']},{l['line_idx']}]", t[:250])
        print('---')
