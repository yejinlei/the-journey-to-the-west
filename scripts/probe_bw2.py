#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 OpenList(AList) 标准 API 列出 bw.shuge.org 分享目录内容。

  py -3 scripts/probe_bw2.py
"""
import json
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

BASE = "https://bw.shuge.org"
CODE = "iOXveWd1"


def post(path, body, extra=None, timeout=25):
    url = BASE + path
    data = json.dumps(body).encode("utf-8")
    h = {"User-Agent": UA, "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.status, r.read().decode("utf-8", "replace")


def get(path, timeout=25, extra=None):
    h = {"User-Agent": UA}
    if extra:
        h.update(extra)
    req = urllib.request.Request(BASE + path, headers=h)
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.status, r.read().decode("utf-8", "replace")


TRIES = [
    ("/api/fs/list", {"path": "/", "password": "", "page": 1, "per_page": 0, "refresh": False}),
    ("/api/fs/list", {"path": "/@s/" + CODE, "password": "", "page": 1, "per_page": 0}),
    ("/api/fs/list", {"path": "/" + CODE, "password": "", "page": 1, "per_page": 0}),
    ("/api/fs/list", {"path": "/@s/" + CODE + "/", "password": "", "page": 1, "per_page": 100}),
    ("/api/public/list", {"path": "/", "password": "", "page": 1, "per_page": 0}),
]

for p, body in TRIES:
    try:
        st, txt = post(p, body)
        head = txt[:400].replace("\n", " ")
        print("POST %-18s body.path=%-22s -> %s  %s"
              % (p, body.get("path"), st, head))
    except Exception as e:
        print("POST %-18s body.path=%-22s -> FAIL %s"
              % (p, body.get("path"), str(e)[:60]))
    print()

# 公开设置 / 自身信息
for p in ["/api/public/settings", "/api/me", "/api/settings"]:
    try:
        st, txt = get(p)
        print("GET %-24s -> %s  %s" % (p, st, txt[:200].replace("\n", " ")))
    except Exception as e:
        print("GET %-24s -> FAIL %s" % (p, str(e)[:50]))
