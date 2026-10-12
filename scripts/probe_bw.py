#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 bw.shuge.org（书格黑白版存储）的接口结构。

  py -3 scripts/probe_bw.py
"""
import re
import ssl
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

URL = "https://bw.shuge.org/@s/iOXveWd1"


def get(url, timeout=30, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.status, dict(r.headers), r.read()


st, hdr, body = get(URL)
print("状态 %s" % st)
print("响应头:")
for k, v in hdr.items():
    print("   %s: %s" % (k, v))
print("\n原始内容（%d 字节）:" % len(body))
print(body.decode("utf-8", "replace"))

html = body.decode("utf-8", "replace")
print("\n" + "=" * 70)
print("script src:")
for s in re.findall(r"<script[^>]*src=[\"']([^\"']+)[\"']", html):
    print("   " + s)
print("link href:")
for s in re.findall(r"<link[^>]*href=[\"']([^\"']+)[\"']", html):
    print("   " + s)

# 试常见的目录/文件接口
print("\n" + "=" * 70)
print("探测常见接口：")
CAND = [
    "https://bw.shuge.org/api/fs/list",
    "https://bw.shuge.org/api/public/list",
    "https://bw.shuge.org/@s/iOXveWd1/",
    "https://bw.shuge.org/manifest.json",
    "https://bw.shuge.org/api/list?path=/iOXveWd1",
]
for u in CAND:
    try:
        s2, h2, b2 = get(u, timeout=15)
        print("  %-52s %s  %d bytes  %s" % (u, s2, len(b2), h2.get("Content-Type", "")))
    except Exception as e:
        print("  %-52s FAIL %s" % (u, str(e)[:40]))
