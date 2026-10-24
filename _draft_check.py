# -*- coding: utf-8 -*-
"""Helper to check draft text lengths against sum(widths)."""
import re

DRAFTS = {}
# (FILL LATER)

with open(r'f:\src\The-Journey-to-the-West\_xkb_merged.txt', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'## p(\d+)\nLINE_COUNT (\d+)\nLINE_WIDTHS \[(.*?)\]\n---\n(.*?)\n===', re.DOTALL)
widths_map = {}
for m in pattern.finditer(content):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    widths_map[p] = ws

for p in [4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18]:
    if p not in DRAFTS:
        continue
    t = DRAFTS[p]
    s = sum(widths_map[p])
    tl = len(t)
    d = tl - s
    pct = 100.0 * d / s
    ok = "OK" if abs(pct) <= 5 else ("OVER" if pct > 0 else "UNDER")
    print(f'p{p}: sum={s} target<={int(s*1.05)} len={tl} diff={d:+d} ({pct:+.2f}%) {ok}')
