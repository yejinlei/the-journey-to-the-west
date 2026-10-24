# -*- coding: utf-8 -*-
"""Iterative text length tuning. Prints diff and character-by-character progress."""
import sys, re
sys.path.insert(0, '.')
from _b5_texts import texts

targets = {63: 480, 65: 482, 66: 484, 67: 434, 69: 85}

for p in [63, 65, 66, 67, 69]:
    t = texts[p]
    tgt = targets[p]
    print(f'\np{p}: len={len(t)} target={tgt} diff={len(t)-tgt:+d}')
    if len(t) != tgt:
        print(f'  {t[:60]}...')
