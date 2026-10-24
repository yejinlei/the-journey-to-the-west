# -*- coding: utf-8 -*-
import json, sys
d = json.loads(open('docs/data/pages/read.json','r',encoding='utf-8').read())
pages = [int(x) for x in sys.argv[1].split(',')]
for l in d['lines']:
    if l.get('edition')!='xinke_pingbi': continue
    if l.get('form_type') not in ('main','verse'): continue
    if l.get('text_zh'): continue
    if l['page_no'] in pages:
        print(f"[{l['page_no']},{l['line_idx']}] === {l['form_type']}")
        print(l['text'])
        print('---')
