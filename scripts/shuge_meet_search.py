#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检索书格 meet 论坛（shuge.org/meet）里的《西游记》相关资源帖。

之前只搜过 /view/ 与 /ebook/，论坛里常有其他馆的高清扫描/网盘线索。
  py -3 scripts/shuge_meet_search.py
"""
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    r = urllib.request.urlopen(req, timeout=timeout, context=CTX)
    return r.read().decode("utf-8", "replace")


QUERIES = ["西游记", "西游", "西遊記", "新说西游记", "西游真诠", "西游证道书", "李卓吾"]
seen = {}

for q in QUERIES:
    url = "https://www.shuge.org/meet/?s=" + urllib.parse.quote(q)
    try:
        html = get(url)
    except Exception as e:
        print("[%s] 失败: %s" % (q, e))
        continue
    # 提取话题链接与标题
    items = re.findall(r"<a[^>]+href=[\"'](https://www\.shuge\.org/meet/topic/\d+[^\"']*)[\"'][^>]*>(.*?)</a>",
                       html, re.S)
    print("=" * 70)
    print("【%s】 命中链接 %d 条" % (q, len(items)))
    for link, title in items[:25]:
        t = re.sub(r"<[^>]+>", "", title)
        t = re.sub(r"\s+", " ", t).strip()
        if not t or len(t) < 4:
            continue
        if link in seen:
            continue
        seen[link] = t
        print("  %s\n      %s" % (t[:70], link))
    time.sleep(1)

print("=" * 70)
print("去重后共 %d 个话题" % len(seen))

# 抓世德堂本专题页，找外链
TARGET = "https://www.shuge.org/meet/topic/13661/"
print("\n" + "=" * 70)
print("抓取世德堂本专题: %s" % TARGET)
try:
    html = get(TARGET)
    print("  长度 %d" % len(html))
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"\s+", " ", txt)
    idx = txt.find("世德堂")
    print("  正文片段: %s" % txt[max(0, idx - 100): idx + 600])
    links = re.findall(r"href=[\"']([^\"']+)[\"']", html)
    ext = [l for l in links if any(k in l for k in
           ("pan.baidu", "aliyundrive", "drive.google", "archive.org",
            "mega.nz", "weiyun", "lanzou", "123pan", "quark"))]
    print("  外链 %d 个:" % len(ext))
    for l in sorted(set(ext))[:20]:
        print("    %s" % l)
except Exception as e:
    print("  失败: %s" % e)
