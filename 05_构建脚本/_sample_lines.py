import json
d = json.load(open(r'docs/data/pages/read.json', encoding='utf-8'))
lines = d.get('lines', [])
pages_wanted = [10, 50, 90]
for p in pages_wanted:
    print('===== PAGE %d =====' % p)
    sub = [l for l in lines if l.get('edition') == 'gubao' and l.get('page_no') == p]
    for l in sub[:12]:
        t = (l.get('text') or '').replace('\n',' ')
        print('  L%d [%s]: %s' % (l.get('line_idx'), l.get('form_type'), t))
    print()
