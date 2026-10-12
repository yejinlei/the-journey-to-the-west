#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析书格下载页 f.shuge.org/dl/... ，找出实际文件链接。

  py -3 scripts/fetch_shuge_dl.py
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

# 世德堂本：新刻出像官板大字西游记（明万历二十年金陵世德堂刊本）
URL = ("https://f.shuge.org/dl/2/?n="
       "%E6%96%B0%E5%88%BB%E5%87%BA%E5%83%8F%E5%AE%98%E6%9D%BF%E5%A4%A7%E5%AD%97"
       "%E8%A5%BF%E6%B8%B8%E8%AE%B0.20%E5%8D%B7.%E6%98%8E.%E5%90%B4%E6%89%BF%E6%81"
       "%A9%E6%92%B0.%E6%98%8E%E4%B8%87%E5%8E%8620%E5%B9%B4%E9%87%91%E9%99%B5%E4%B8"
       "%96%E5%BE%B7%E5%A0%82%E5%88%8A%E6%9C%AC.%E7%81%B0%E5%BA%A6%E8%83%B6%E7%89%87"
       "&d=dazxyjp&tn=&j=dwSv&hb=iOXveWd1&bd=1Z88-UeqVXfRVIEIwDXuXcA&ay=1CGjQHBdwwe&m=&e=")

req = urllib.request.Request(URL, headers={"User-Agent": UA})
html = urllib.request.urlopen(req, timeout=30, context=CTX).read().decode("utf-8", "replace")
print("页面长度 %d" % len(html))

clean = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
txt = re.sub(r"<[^>]+>", "\n", clean)
txt = re.sub(r"\n{2,}", "\n", txt)
lines = [l.strip() for l in txt.split("\n") if len(l.strip()) > 1]
print("-" * 70)
print("页面文本：")
for l in lines[:60]:
    print("  " + l[:160])

print("-" * 70)
print("所有链接：")
links = re.findall(r"href=[\"']([^\"']+)[\"']", html)
for l in sorted(set(links))[:40]:
    print("  " + l[:170])

print("-" * 70)
print("疑似文件链接（含下载关键词）：")
KEY = (".zip", ".rar", ".7z", ".pdf", "download", "dl=", "file=", "oss", "cdn",
       "shuge.org/s/", "f.shuge.org")
cand = sorted(set(l for l in links if any(k in l.lower() for k in KEY)))
for l in cand[:40]:
    print("  " + l[:170])
print("  共 %d 条" % len(cand))

# 页面里可能用 JS 变量拼下载地址，把整页里的 url 形态抓出来
js = re.findall(r"[\"'](https?://[^\"']{20,200})[\"']", html)
print("-" * 70)
print("页面中出现的绝对 URL：")
for u in sorted(set(js))[:40]:
    print("  " + u[:170])
