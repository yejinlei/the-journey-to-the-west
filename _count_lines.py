# -*- coding: utf-8 -*-
"""Helper to count lengths of lines given target widths."""
import sys
import json

# Load lines from file
lines = [l.rstrip('\n') for l in open(sys.argv[1], 'r', encoding='utf-8') if l.strip()]
widths = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None

for i, l in enumerate(lines):
    w = widths[i] if widths and i < len(widths) else '?'
    flag = '' if (widths and i < len(widths) and len(l) == widths[i]) else ' <-- MISMATCH'
    print(f'{i:2d}: want {w} got {len(l)}{flag} :: {l}')
