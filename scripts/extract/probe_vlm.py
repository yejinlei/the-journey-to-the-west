#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VLM 可用性冒烟测试。

用法：
  set SENSENOVA_API_KEY=sk-xxx
  py -3 scripts/extract/probe_vlm.py                    # 纯文本一次
  py -3 scripts/extract/probe_vlm.py --image <jpg>       # 加一张图
  py -3 scripts/extract/probe_vlm.py --sample            # 从已下页里挑一张试
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vlm_client import BASE_URL, MODEL, API_KEY, image_messages, text_messages, vlm_chat

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]


def pick_sample():
    """挑一张书格李评本（分辨率清晰、样本目录）当试图。"""
    cands = sorted((ROOT / "book" / "scans" / "李评本").glob("xi_you_ji_yi*.jpg"))
    if cands:
        return cands[0]
    cands = sorted((ROOT / "book" / "scans" / "李评本_Gallica4034").glob("p*.jpg"))
    return cands[0] if cands else None


ap = argparse.ArgumentParser()
ap.add_argument("--image")
ap.add_argument("--sample", action="store_true")
args = ap.parse_args()

img = args.image
if args.sample and not img:
    img = pick_sample()

print(f"BASE_URL = {BASE_URL}")
print(f"MODEL    = {MODEL}")
print(f"KEY      = ***{API_KEY[-6:] if API_KEY else '(missing)'}")

# 1) 文本冒烟
t0 = time.time()
try:
    r = vlm_chat(text_messages("You are helpful.", "回复两个字：正常"), max_tokens=500, timeout=60)
    print(f"\n[文本冒烟] {time.time()-t0:.1f}s -> {r[:200]!r}")
except Exception as e:
    print(f"\n[文本冒烟] FAIL: {e}")
    sys.exit(1)

# 2) 图冒烟
if img:
    print(f"\n[图像冒烟] 输入: {img}")
    prompt = (
        "这是一页中国古代文献图像。请只用 JSON 返回以下信息：\n"
        '{"has_text": true, "vertical_layout": true, "page_size_estimate": "...", "first_20_chars": "..."}'
    )
    t0 = time.time()
    try:
        r = vlm_chat(image_messages("You are an expert OCR assistant for classical Chinese texts.", prompt, [img]),
                     max_tokens=1500, timeout=180)
        print(f"[图像冒烟] {time.time()-t0:.1f}s -> {r[:1200]}")
    except Exception as e:
        print(f"[图像冒烟] FAIL: {e}")
