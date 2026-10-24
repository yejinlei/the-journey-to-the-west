# -*- coding: utf-8 -*-
import json
d = json.load(open('_xkb_batch1.json','r',encoding='utf-8'))
print(f'Total entries: {len(d)}')
for e in d:
    t = e['text_zh']
    print(f"p{e['page']}: type={type(t).__name__}")
    if isinstance(t, list):
        print(f"  list length: {len(t)}, line lengths: {[len(x) for x in t]}")
    else:
        print(f"  string length: {len(t)}")
        # Check if it has newlines
        if '\n' in t:
            print(f"  contains {t.count(chr(10))} newlines")
        print(f"  first 50 chars: {t[:50]!r}")
