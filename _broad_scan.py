"""广扫描：所有 json 里的 header 元数据污染"""
import json, glob, re
from pathlib import Path

patterns = [
    ('notes =', r'notes\s*='),
    ('author =', r'author\s*='),
    ('previous =', r'previous\s*='),
    ('next =', r'next\s*='),
    ('}}', r'\}\}'),
    ('{{header', r'\{\{header'),
    ('{{另', r'\{\{另'),
    ('管道符| =', r'\|\s*\w+\s*='),
]

# 扫 read.json（全库源）
print("=== docs/data/pages/read.json ===")
d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
for pat_name, pat in patterns:
    hits = 0
    samples = []
    for l in d['lines']:
        for fld in ('text', 'text_zh'):
            v = l.get(fld) or ''
            if re.search(pat, v):
                hits += 1
                if len(samples) < 2:
                    samples.append((l['edition'], l['page_no'], l['line_idx'], fld, v[:100]))
    if hits:
        print(f"  {pat_name}: {hits}")
        for s in samples:
            print(f"    {s}")

# 扫前端 9 个 JSON
print("\n=== 06_Web前端/data/read/*.json ===")
for p in sorted(glob.glob('06_Web前端/data/read/*.json')):
    d2 = json.loads(Path(p).read_text(encoding='utf-8'))
    if isinstance(d2, dict):
        continue
    for pat_name, pat in patterns:
        hits = 0
        samples = []
        for ch in d2:
            for ln in ch.get('lines', []):
                for fld in ('x', 'z'):
                    v = ln.get(fld) or ''
                    if re.search(pat, v):
                        hits += 1
                        if len(samples) < 2:
                            samples.append((ch['l'], ln['i'], fld, v[:100]))
        if hits:
            print(f"  {Path(p).name} / {pat_name}: {hits}")
            for s in samples:
                print(f"    {s}")
