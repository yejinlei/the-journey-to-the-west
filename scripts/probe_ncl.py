#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测台湾國圖古籍影像检索系统 NCLSearch 的结构与检索接口。

  py -3 scripts/probe_ncl.py
"""
import re
import ssl
import sys
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

BASE = "http://rbook.ncl.edu.tw/NCLSearch"


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.read().decode("utf-8", "replace"), r.geturl()


def show(tag, url):
    print("=" * 70)
    print("【%s】 %s" % (tag, url))
    try:
        html, final = get(url)
    except Exception as e:
        print("  失败: %s" % e)
        return None
    print("  最终URL: %s   长度 %d" % (final, len(html)))
    actions = re.findall(r"<form[^>]*action=[\"']([^\"']*)[\"']", html, re.I)
    inputs = re.findall(r"<input[^>]*name=[\"']([^\"']*)[\"']", html, re.I)
    if actions:
        print("  form action: %s" % ", ".join(actions[:5]))
    if inputs:
        print("  input name : %s" % ", ".join(sorted(set(inputs))[:16]))
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"\s+", " ", txt).strip()
    print("  正文片段: %s" % txt[:300])
    # 是否命中西游记
    hit = html.count("西遊記") or html.count("西游记")
    if hit:
        print("  >>> 命中西遊記 %d 次" % hit)
    return html


show("NCLSearch 首页", BASE + "/")
show("NCLSearch 检索(西遊記)", BASE + "/Search?keyword=" + urllib.parse.quote("西遊記"))
show("NCLSearch 检索(西游记)", BASE + "/SimpleSearch?query=" + urllib.parse.quote("西遊記"))
