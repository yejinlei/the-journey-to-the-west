import json, glob
from pathlib import Path

paths = sorted(glob.glob('06_Web前端/data/read/*.json'))
total_bad = 0
for p in paths:
    d = json.loads(Path(p).read_text(encoding='utf-8'))
    if isinstance(d, dict):
        continue
    bad = 0
    samples = []
    for ch in d:
        for ln in ch.get('lines', []):
            for fld in ('x', 'z'):
                v = ln.get(fld) or ''
                if 'notes' in v or '}}' in v or 'author =' in v or 'previous =' in v or 'next =' in v or '|' in v[:80]:
                    bad += 1
                    if len(samples) < 3:
                        samples.append((ch['l'], ln['i'], fld, v[:120]))
    print(f"  {Path(p).name}: {bad} 条残留")
    for s in samples:
        print(f"    {s}")
    total_bad += bad

print(f"\n总计残留: {total_bad}")
