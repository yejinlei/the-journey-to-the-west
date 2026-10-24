# -*- coding: utf-8 -*-
"""Build _xkb_batch5.json.
text_zh is a LIST of lines; each line[i].__len__() == widths[i].
Total char count must equal sum(widths).
Strategy: build continuous text, then segment by widths.
"""
import json, re

# Read merged to grab widths
merged = open('_xkb_merged.txt', 'r', encoding='utf-8').read()
widths_map = {}
for m in re.finditer(r'## p(\d+)\nLINE_COUNT (\d+)\nLINE_WIDTHS \[(.*?)\]\n---', merged):
    p = int(m.group(1))
    widths_map[p] = [int(x) for x in m.group(3).split(',')]

# Continuous modern vernacular texts (no punctuation, exact char count == sum(widths))
texts = {
    # 22*18 + 21*4 = 396 + 84 = 480
    63: "",
    # 22 + 21 + 22*16 + 21 + 22*3 = 22+21+352+21+66 = 482
    65: "",
    # 22*22 = 484
    66: "",
    # 24+22+23+22+22+10+22+21+14+22+22+22+22+22+22+22+22+22+18+15+22+1 = 434
    67: "",
    # 11+9+20+14+9+2+2+1*17 = 85
    69: "",
}

def check_and_segment(p):
    w = widths_map[p]
    target = sum(w)
    t = texts[p]
    n = len(t)
    status = 'OK' if n == target else f'DIFF {n-target:+d}'
    print(f'p{p}: len={n}, target={target}, {status}')
    if n != target:
        return None
    lines = []
    idx = 0
    for wid in w:
        lines.append(t[idx:idx+wid])
        idx += wid
    return lines

# --- Iterate to hit lengths ---
import sys

if __name__ == '__main__':
    # Load candidate texts from a separate module if available
    try:
        from _batch5_texts import texts as src_texts
        texts.clear()
        texts.update(src_texts)
    except ImportError:
        print('no _batch5_texts module, using empty placeholders')

    for p in [63, 65, 66, 67, 69]:
        check_and_segment(p)
