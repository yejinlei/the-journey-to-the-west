#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在书格（主站 + 论坛）搜索《西游记》相关资源。

之前 ?s= 对论坛无效（bbPress 用 bbp_search），这里试多种形式并比对结果。
  py -3 scripts/shuge_forum_search.py
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
    return urllib.request.urlopen(req, timeout=timeout, context=CTX).read().decode("utf-8", "replace")


def topics(html):
    items = re.findall(
        r"<a[^>]+href=[\"'](https://www\.shuge\.org/(?:meet/topic/\d+|ebook/[^\"']+|view/[^\"']+)[^\"']*)[\"'][^>]*>(.*?)</a>",
        html, re.S)
    out = []
    for link, title in items:
        t = re.sub(r"<[^>]+>", "", title)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) >= 4:
            out.append((t, link))
    return out


QUERIES = ["西遊記", "西游记", "西游", "新說西遊記", "西遊真詮", "西遊證道書", "李卓吾"]
FORMS = [
    ("meet bbp_search", "https://www.shuge.org/meet/?bbp_search=%s"),
    ("meet search path", "https://www.shuge.org/meet/search/%s/"),
    ("site ?s=", "https://www.shuge.org/?s=%s"),
]

for form_name, tpl in FORMS:
    print("=" * 74)
    print("检索形式: %s" % form_name)
    agg = {}
    for q in QUERIES:
        url = tpl % urllib.parse.quote(q)
        try:
            html = get(url)
        except Exception as e:
            print("  [%s] 失败 %s" % (q, str(e)[:60]))
            continue
        ts = topics(html)
        rel = [(t, l) for t, l in ts if ("西游" in t or "西遊" in t or "西游记" in t)]
        print("  [%s] 链接 %d 条，其中西游相关 %d 条" % (q, len(ts), len(rel)))
        for t, l in rel[:12]:
            if l in agg:
                continue
            agg[l] = t
            print("      %s\n        %s" % (t[:76], l))
        time.sleep(0.8)
    print("  去重后 %d 条" % len(agg))
