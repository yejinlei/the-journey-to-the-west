import json
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
for l in d['lines']:
    if l.get('edition') == 'xiyou_yuanzhi' and l['page_no'] == 1:
        if l['line_idx'] in (1, 4, 7, 10, 13, 17, 22):
            text = l.get('text', '')
            print(f"l{l['line_idx']}: chars={[hex(ord(c)) for c in text]}  repr={repr(text)}")
