# -*- coding: utf-8 -*-
"""Tune drafts to exact target lengths. Interactive."""
import re, sys, json
sys.stdout.reconfigure(encoding='utf-8')

def parse_source():
    s = open('_xkb_merged.txt', encoding='utf-8').read()
    d = {}
    for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]', s):
        p = int(m.group(1))
        ws = [int(x) for x in m.group(3).split(',')]
        d[p] = ws
    return d

# Load drafts from the current build script's DRAFTS_RAW / P30_BLOCKS
with open('_build_batch2.py', encoding='utf-8') as f:
    code = f.read()
ns = {}
exec(code.replace("if __name__ == '__main__':", "if False:"), ns)
DRAFTS_RAW = ns.get('DRAFTS_RAW', {})
P30_BLOCKS = ns.get('P30_BLOCKS', [])

src = parse_source()
print("Page | Expected | Got    | Diff")
print("-" * 40)
for p in [20, 21, 22, 23, 25, 26, 28, 30, 32, 33, 34]:
    e = sum(src[p])
    if p == 30:
        got = sum(len(b) for b in P30_BLOCKS)
        print(f"p{p:2d} | {e:8d} | {got:6d} | {got-e:+d}")
        for i, (w, b) in enumerate(zip(src[p], P30_BLOCKS)):
            print(f"   b{i}: expected={w} got={len(b)} diff={len(b)-w:+d}")
    else:
        got = len(DRAFTS_RAW[p].strip())
        print(f"p{p:2d} | {e:8d} | {got:6d} | {got-e:+d}")
