import json, glob, re
from pathlib import Path

# 全库扫描：任何含 'notes' 的文本
print("=== docs/data/pages/read.json ===")
d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
hits = 0
for l in d['lines']:
    for fld in ('text', 'text_zh'):
        v = l.get(fld) or ''
        if re.search(r'\bnotes\b', v, re.I):
            print(f"  [{l['edition']}] p{l['page_no']}#{l['line_idx']} {fld}: {v[:180]!r}")
            hits += 1
print(f"  hits: {hits}")

print("\n=== 06_Web前端/data/read/*.json ===")
for p in sorted(glob.glob('06_Web前端/data/read/*.json')):
    d2 = json.loads(Path(p).read_text(encoding='utf-8'))
    if isinstance(d2, dict): continue
    hits = 0
    for ch in d2:
        for ln in ch.get('lines', []):
            for fld in ('x', 'z'):
                v = ln.get(fld) or ''
                if re.search(r'\bnotes\b', v, re.I) or '}}' in v or '{{header' in v:
                    print(f"  {Path(p).name} ch={ch['l']}#{ln['i']} {fld}: {v[:180]!r}")
                    hits += 1
    print(f"  {Path(p).name} total: {hits}")
