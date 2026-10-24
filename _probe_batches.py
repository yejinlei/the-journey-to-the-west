import json, os
for i in range(1, 6):
    p = f'_xkb_batch{i}.json'
    if not os.path.exists(p):
        print(p, 'MISSING'); continue
    d = json.loads(open(p, 'r', encoding='utf-8').read())
    if isinstance(d, list):
        print(p, 'list', 'len=', len(d), 'keys=', list(d[0].keys()) if d else 'empty')
        if d:
            e = d[0]
            print('   page=', e.get('page_no'), 'text_zh[:80]=', (e.get('text_zh') or '')[:80])
    else:
        print(p, 'dict', list(d.keys())[:8])
