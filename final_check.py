# -*- coding: utf-8 -*-
import json
d = json.load(open('_xkb_batch5.json', encoding='utf-8'))
b1 = json.load(open('_xkb_batch1.json', encoding='utf-8'))
print(f"batch5 pages: {len(d)}")
print(f"batch5 total lines: {sum(len(x['widths']) for x in d)}")
for x in d:
    print(f"  p{x['page']}: lines={len(x['widths'])}, type(text_zh)={type(x['text_zh']).__name__}, len={len(x['text_zh'])}")
print()
print("batch1 sample format check:")
for x in b1[:3]:
    print(f"  p{x['page']}: type(text_zh)={type(x['text_zh']).__name__}, len={len(x['text_zh'])}, sum(widths)={sum(x['widths'])}")
