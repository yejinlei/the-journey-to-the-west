import json
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
targets = {(1,1),(1,4),(1,7),(1,10),(1,13),(1,17),(1,22)}
print("Total lines on page 1 of xiyou_yuanzhi:")
for l in d['lines']:
    if l.get('edition') == 'xiyou_yuanzhi' and l.get('form_type') in ('main','verse') and l['page_no'] == 1:
        k = (l['page_no'], l['line_idx'])
        zh = l.get('text_zh','')
        marker = ' *' if k in targets else ''
        print(f"  l{k[1]} form={l.get('form_type')} len={len(l.get('text',''))} zhlen={len(zh)}{marker}  preview='{l.get('text','')[:40]}'")

print("\nAll '##' lines across all editions:")
for l in d['lines']:
    if '##' in (l.get('text') or ''):
        print(f"  [{l['edition']}] p{l['page_no']}-{l['line_idx']} form={l.get('form_type')} text='{l.get('text')[:20]}'")
