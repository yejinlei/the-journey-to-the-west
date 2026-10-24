#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 Gallica（法国国家图书馆）检索《西游记》各版本，输出 ark 标识符清单。"""
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 汇评本 14 个大系统 / 9 大评点系统对应的检索词
QUERIES = [
    "西遊記",
    "西游真诠", "西遊真詮",
    "新說西遊記",
    "西遊原旨",
    "通易西遊正旨",
    "西遊記評注",
    "西遊記記",
    "世德堂",
    "西遊證道書",
    "增評西遊證道大奇書",
    "唐三藏",
]


def sru(query, maxrec=30):
    url = ("https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2"
           "&maximumRecords=%d&query=" % maxrec) + urllib.parse.quote('gallica all "%s"' % query)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")


records = {}
for q in QUERIES:
    try:
        body = sru(q)
    except Exception as e:
        print("[%s] FAIL %s" % (q, str(e)[:70]))
        continue
    blocks = re.split(r"<srw:record(?:\s[^>]*)?>", body)[1:]
    n = 0
    for b in blocks:
        m_id = re.search(r"<dc:identifier>(.*?)</dc:identifier>", b, re.S)
        m_ti = re.search(r"<dc:title>(.*?)</dc:title>", b, re.S)
        if not m_id:
            continue
        ark = m_id.group(1).strip()
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m_ti.group(1))).strip() if m_ti else ""
        if ark not in records:
            records[ark] = (title, q)
            n += 1
    print("[%s] 命中 %d 条（新增 %d）" % (q, len(blocks), n))

print("\n=== 全部记录 %d 条 ===" % len(records))
out = []
for ark, (title, q) in records.items():
    out.append((ark, title, q))
out.sort(key=lambda x: x[2])
for ark, title, q in out:
    print("\n  ark: %s" % ark)
    print("  标题: %s" % title[:150])
    print("  来源词: %s" % q)
