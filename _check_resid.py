import json, re, sys
from pathlib import Path

SRC = Path('docs/data/pages/read.json')
d = json.loads(SRC.read_text(encoding='utf-8'))

META_KEYS = ('author','previous','next','notes','title','chapter')
SPLIT = ' | '
RE_META = re.compile(r'\b(' + '|'.join(META_KEYS) + r')\s*=')

print(f"总行数: {len(d['lines'])}")
print(f"gubao 行数: {sum(1 for l in d['lines'] if l.get('edition')=='gubao')}")

found = []
for i, l in enumerate(d['lines']):
    for fld in ('text', 'text_zh'):
        v = l.get(fld) or ''
        if 'notes' in v or '}}' in v or 'author =' in v or 'previous =' in v or 'next =' in v:
            found.append((l.get('edition'), l.get('page_no'), l.get('line_idx'), fld, v))

print(f"\n残留条数: {len(found)}")
for e, p, i, f, v in found[:30]:
    print(f"  [{e}] p{p}#{i} {f}: {v[:200]}")

# 也扫 gubao.json
GUBAO = Path('06_Web前端/data/read/gubao.json')
if GUBAO.exists():
    d2 = json.loads(GUBAO.read_text(encoding='utf-8'))
    print(f"\n--- gubao.json ---")
    for i, l in enumerate(d2['lines']):
        for fld in ('text', 'text_zh'):
            v = l.get(fld) or ''
            if 'notes' in v or '}}' in v or 'author =' in v or 'previous =' in v or 'next =' in v:
                print(f"  p{l.get('page_no')}#{l.get('line_idx')} {fld}: {v[:200]}")
