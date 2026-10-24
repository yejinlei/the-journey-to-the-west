import json
from collections import defaultdict
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
c = defaultdict(lambda: {'total': 0, 'done': 0})
for l in d['lines']:
    if l.get('form_type') in ('main', 'verse'):
        c[l['edition']]['total'] += 1
        if l.get('text_zh'):
            c[l['edition']]['done'] += 1
for e in sorted(c):
    t = c[e]['total']; dn = c[e]['done']
    print(f'{e}: done {dn}/{t} remain {t-dn}')
