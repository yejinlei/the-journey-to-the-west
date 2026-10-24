# -*- coding: utf-8 -*-
import json, sys
d=json.load(open('docs/data/pages/read.json',encoding='utf-8'))
ed=sys.argv[1]; fts=sys.argv[2].split(',')
n_total=0; n_show=0
for l in d['lines']:
    if l.get('edition')!=ed: continue
    if l.get('form_type') not in fts: continue
    if l.get('text_zh'): continue
    n_total+=1
    if n_show>=int(sys.argv[3]) if len(sys.argv)>3 else False:
        break
    t=(l.get('text') or '')
    print(f"[{l['page_no']},{l['line_idx']}] {l['form_type']:7s} | {t}")
    n_show+=1
print(f"# total={n_total}", file=sys.stderr)
