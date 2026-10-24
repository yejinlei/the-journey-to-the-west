import json
from collections import defaultdict
EDITION = 'xu_xiyouji'
d = json.load(open('docs/data/pages/read.json', encoding='utf-8'))
todo_pages = defaultdict(int)
for l in d['lines']:
    if l.get('edition') == EDITION and l.get('form_type') in ('main','verse'):
        if not l.get('text_zh'):
            todo_pages[l['page_no']] += 1
print(f'{EDITION}: {len(todo_pages)} pages, {sum(todo_pages.values())} lines')
pages = sorted(todo_pages.keys())
print(f'range: {pages[0]}..{pages[-1]}')
# plan batches of 200-350 lines
chunks = []
cur = {'start': None, 'end': None, 'count': 0}
for p in pages:
    if cur['start'] is None:
        cur['start'] = p
    cur['end'] = p
    cur['count'] += todo_pages[p]
    if cur['count'] >= 300:
        chunks.append(dict(cur))
        cur = {'start': None, 'end': None, 'count': 0}
if cur['start'] is not None:
    chunks.append(dict(cur))
print(f'{len(chunks)} chunks:')
for c in chunks:
    print(f"  {c['start']}-{c['end']}: {c['count']} 行")
