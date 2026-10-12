#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取各古籍库首页，提取检索表单的 action 与参数名，以便构造检索 URL。

  py -3 scripts/probe_search_form.py
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

SITES = [
    ("京都大学貴重資料", "https://rmda.kulib.kyoto-u.ac.jp/"),
    ("早稻田古典籍DB", "https://www.wul.waseda.ac.jp/kotenseki/"),
    ("台湾國圖古籍影像", "https://rbook.ncl.edu.tw/"),
    ("東大デジタルアーカイブ", "https://da.dl.itc.u-tokyo.ac.jp/"),
    ("中研院傅斯年圖書館", "https://lib.ihp.sinica.edu.tw/"),
]


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.read().decode("utf-8", "replace")


for name, url in SITES:
    print("=" * 70)
    print("【%s】 %s" % (name, url))
    try:
        html = get(url)
    except Exception as e:
        print("  抓取失败: %s" % e)
        continue
    print("  长度 %d" % len(html))
    forms = re.findall(r"<form[^>]*>", html, re.I)
    actions = re.findall(r"<form[^>]*action=[\"']([^\"']*)[\"']", html, re.I)
    inputs = re.findall(r"<input[^>]*name=[\"']([^\"']*)[\"']", html, re.I)
    print("  form 数: %d" % len(forms))
    for a in actions[:6]:
        print("    action: %s" % a)
    if inputs:
        print("    input name: %s" % ", ".join(sorted(set(inputs))[:14]))
    # 顺带看有没有明显的搜索入口链接
    links = re.findall(r"href=[\"']([^\"']*search[^\"']*)[\"']", html, re.I)
    for l in sorted(set(links))[:8]:
        print("    search链接: %s" % l)
    if len(html) < 2000:
        print("  页面正文片段: %s" % re.sub(r"<[^>]+>", " ", html)[:400])
