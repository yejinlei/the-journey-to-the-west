#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对 SSL 证书校验失败的站点，忽略证书重试，确认是否真的可达。

  py -3 scripts/probe_ssl.py
"""
import ssl
import sys
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

SITES = [
    ("早稻田大学图书馆", "https://www.wul.waseda.ac.jp/"),
    ("早稻田古典籍DB", "https://www.wul.waseda.ac.jp/kotenseki/"),
    ("京都大学貴重資料", "https://rmda.kulib.kyoto-u.ac.jp/"),
    ("台湾國圖古籍影像", "https://rbook.ncl.edu.tw/"),
    ("台湾國圖", "https://www.ncl.edu.tw/"),
    ("柏林国家图书馆", "https://digital.staatsbibliothek-berlin.de/"),
    ("東大デジタルアーカイブ", "https://da.dl.itc.u-tokyo.ac.jp/"),
    ("中研院傅斯年圖書館", "https://lib.ihp.sinica.edu.tw/"),
]


def probe(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
        body = r.read(200000)
        return r.status, len(body), int((time.time() - t) * 1000)
    except Exception as e:
        return str(e)[:46], 0, int((time.time() - t) * 1000)


for name, url in SITES:
    st, n, ms = probe(url)
    flag = "OK " if st == 200 else "   "
    print("%s %-20s %-48s %6d bytes %dms" % (flag, name, str(st), n, ms))
    time.sleep(0.3)
