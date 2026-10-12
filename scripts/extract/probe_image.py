#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图像 OCR 冒烟：测试不同 max_tokens 下图像 content 是否非空。"""
import os, sys, time, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SENSENOVA_API_KEY", "sk-MUdQGuADpncGwjHHPSjLAqWFTlnZUfUI")
from vlm_client import vlm_chat, image_messages

# 用已知存在的一页书格李评本作为样本
sample = r"f:\src\The-Journey-to-the-West\book\scans\新刻全像批评西游记\p0050.jpg"
if not os.path.exists(sample):
    print("样本不存在"); sys.exit(1)
print(f"样本: {sample}")
print(f"文件大小: {os.path.getsize(sample)/1024:.1f} KB")

SYSTEM = "你是精通明清刻本的 OCR 引擎。请忠实转录图中的所有可见文字（含正文、回目、行外小字/眉批/夹批/回前评/回后评），保持从上到下、从右到左的顺序。"
USER = "请把这页的所有文字转录出来，只输出文字，不要评论。"

for mt in (2000, 4000, 8000):
    t0 = time.time()
    try:
        r = vlm_chat(image_messages(SYSTEM, USER, [sample]),
                     max_tokens=mt, timeout=300)
        dt = time.time() - t0
        n = len(r) if r else 0
        print(f"[max_tokens={mt}] {dt:.1f}s 返回长度={n}")
        if n:
            print("--- 前 300 字符 ---")
            print(r[:300])
            print("---")
            break
    except Exception as e:
        print(f"[max_tokens={mt}] 失败: {e}")
