#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断 Gallica 403：测试不同请求头是否被接受。"""
import sys
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA_CHROME = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
UA_FF = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
         "Gecko/20100101 Firefox/125.0")

ARK = "btv1b9006390m"
URL = "https://gallica.bnf.fr/iiif/ark:/12148/%s/manifest.json" % ARK

VARIANTS = [
    ("无头", {}),
    ("仅UA-Chrome", {"User-Agent": UA_CHROME}),
    ("仅UA-Firefox", {"User-Agent": UA_FF}),
    ("完整浏览器头", {
        "User-Agent": UA_CHROME,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Referer": "https://gallica.bnf.fr/",
        "Origin": "https://gallica.bnf.fr",
        "Connection": "keep-alive",
    }),
]

for name, headers in VARIANTS:
    try:
        req = urllib.request.Request(URL, headers=headers)
        r = urllib.request.urlopen(req, timeout=30)
        body = r.read()
        print("%-14s OK  %s  %d bytes" % (name, r.status, len(body)), flush=True)
    except Exception as e:
        print("%-14s FAIL %s" % (name, e), flush=True)
    time.sleep(3)

# 顺带测根域，判断是整站封禁还是仅 IIIF
for label, u in [("根域", "https://gallica.bnf.fr/"),
                 ("ark页", "https://gallica.bnf.fr/ark:/12148/%s" % ARK)]:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA_CHROME})
        r = urllib.request.urlopen(req, timeout=30)
        print("%-14s OK  %s" % (label, r.status), flush=True)
    except Exception as e:
        print("%-14s FAIL %s" % (label, e), flush=True)
    time.sleep(3)
