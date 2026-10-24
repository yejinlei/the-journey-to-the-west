# -*- coding: utf-8 -*-
"""Verify batch5 format matches batch1."""
import json

b1 = json.load(open('_xkb_batch1.json','r',encoding='utf-8'))
b5 = json.load(open('_xkb_batch5.json','r',encoding='utf-8'))

print('=== batch1 format ===')
for e in b1[:3]:
    t = e['text_zh']
    print(f"  p{e['page']}: type={type(t).__name__}, keys={list(e.keys())}")

print('\n=== batch5 format ===')
for e in b5:
    t = e['text_zh']
    print(f"  p{e['page']}: type={type(t).__name__}, len={len(t)}, keys={list(e.keys())}")
