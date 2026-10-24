# -*- coding: utf-8 -*-
"""检查 xinke_pingbi title/poem 的 text_zh 状态"""
import json
d = json.load(open('docs/data/pages/read.json','r',encoding='utf-8'))
rows = [l for l in d['lines'] if l.get('edition')=='xinke_pingbi' and l.get('form_type') in ('title','poem')]
done = [r for r in rows if r.get('text_zh')]
print(f'total title+poem: {len(rows)}, has text_zh: {len(done)}')
for r in rows:
    z = r.get('text_zh','')
    print(f"({r['page_no']},{r['line_idx']})[{r['form_type']}] src={r['text']!r}  zh={'(empty)' if not z else z!r}")
