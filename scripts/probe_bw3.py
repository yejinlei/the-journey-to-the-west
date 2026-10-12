#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取 bw.shuge.org 分享文件 iOXveWd1 的真实下载地址。

  py -3 scripts/probe_bw3.py
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


def post(path, body, timeout=25):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST",
                                 headers={"User-Agent": UA,
                                          "Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.status, r.read().decode("utf-8", "replace")


def head(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.status, dict(r.headers)


print("=== /api/fs/get ===")
for p in ["/@s/" + CODE, "@s/" + CODE, "/" + CODE]:
    try:
        st, txt = post("/api/fs/get", {"path": p, "password": ""})
        d = json.loads(txt)
        print("path=%-18s -> code=%s %s" % (p, d.get("code"), d.get("message", "")))
        if d.get("code") == 200:
            print(json.dumps(d["data"], ensure_ascii=False, indent=2)[:1800])
            break
    except Exception as e:
        print("path=%-18s -> FAIL %s" % (p, str(e)[:70]))

print("\n=== 常见下载路径 ===")
for u in ["/d/@s/" + CODE, "/p/@s/" + CODE, "/d/" + CODE, "/api/raw/@s/" + CODE,
          "/@s/" + CODE + "?download=1", "/d/@s/" + CODE + "/"]:
    try:
        st, h = head(BASE + u)
        ct = h.get("Content-Type", "")
        cl = h.get("Content-Length", "")
        cd = h.get("Content-Disposition", "")
        print("%-34s -> %s  %s  len=%s  %s" % (u, st, ct[:26], cl, cd[:70]))
    except Exception as e:
        print("%-34s -> FAIL %s" % (u, str(e)[:50]))
