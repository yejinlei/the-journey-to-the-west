#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VLM OCR 冒烟（新精简 prompt）"""
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SENSENOVA_API_KEY", "sk-MUdQGuADpncGwjHHPSjLAqWFTlnZUfUI")
from vlm_client import vlm_chat, image_messages
from schema import SYSTEM_OCR, USER_OCR

sample = r"f:\src\The-Journey-to-the-West\book\scans\新刻全像批评西游记\p0050.jpg"
t0 = time.time()
raw = vlm_chat(image_messages(SYSTEM_OCR, USER_OCR, [sample]),
               max_tokens=4000, timeout=300)
dt = time.time() - t0
print(f"{dt:.1f}s  长度={len(raw)}")
print("--- 前 400 字符 ---")
print(raw[:400] if raw else "(EMPTY)")
print("--- 后 200 字符 ---")
print(raw[-200:] if raw else "")

# 尝试解析
def parse(t):
    t = t.strip()
    t = t.strip("`").strip()
    if t.startswith("json"): t = t[4:].lstrip()
    try: return json.loads(t)
    except: 
        s = t.find("{"); e = t.rfind("}")
        if s>=0 and e>s:
            try: return json.loads(t[s:e+1])
            except: return None
    return None

obj = parse(raw)
if obj:
    print(f"\n解析成功：layout={obj.get('layout')} lines={len(obj.get('lines',[]))}")
    for i, l in enumerate(obj.get("lines", [])[:5]):
        print(f"  [{i}] type={l.get('type')} 前40={l.get('text','')[:40]}")
else:
    print("解析失败")
