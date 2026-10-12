#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试给定代理能否访问 Gallica，并测速。

  py -3 scripts/test_proxy.py --proxy 127.0.0.1:7890
  py -3 scripts/test_proxy.py --proxy http://127.0.0.1:7890 --download
"""
import argparse
import os
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
ARK = "btv1b9006390m"
MANIFEST = "https://gallica.bnf.fr/iiif/ark:/12148/%s/manifest.json" % ARK
IMG = "https://gallica.bnf.fr/iiif/ark:/12148/%s/f1/full/1200,/0/native.jpg" % ARK

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ap = argparse.ArgumentParser()
ap.add_argument("--proxy", help="如 127.0.0.1:7890")
ap.add_argument("--download", action="store_true", help="额外测一张图的下载速度")
args = ap.parse_args()


def opener():
    d = {}
    if args.proxy:
        p = args.proxy if "://" in args.proxy else "http://" + args.proxy
        d["https"] = p
        d["http"] = p
    hp = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if hp:
        d["https"] = hp
    if not d:
        print("未指定代理，走直连（大概率 403）")
    else:
        print("使用代理: %s" % d)
    h = [urllib.request.ProxyHandler(d)] if d else []
    return urllib.request.build_opener(*h)


op = opener()


def get(url, timeout=40):
    t = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    r = op.open(req, timeout=timeout)
    body = r.read()
    return r.status, len(body), time.time() - t


print("-" * 56)
ok_all = True
for name, u in [("根域", "https://gallica.bnf.fr/"), ("manifest", MANIFEST)]:
    try:
        st, n, dt = get(u)
        print("%-10s %s  %d bytes  %.1fs" % (name, st, n, dt))
        if st != 200:
            ok_all = False
    except Exception as e:
        print("%-10s FAIL %s" % (name, e))
        ok_all = False

if ok_all and args.download:
    try:
        st, n, dt = get(IMG, timeout=90)
        print("%-10s %s  %.1f KB  %.1fs  -> %.0f KB/s"
              % ("图片", st, n / 1024, dt, n / 1024 / dt))
    except Exception as e:
        print("图片 FAIL %s" % e)
print("-" * 56)
print("结论：" + ("代理可用，可以开始补下。" if ok_all else "仍然不可用，换一个出口 IP 再试。"))
