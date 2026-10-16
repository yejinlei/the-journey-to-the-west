# -*- coding: utf-8 -*-
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


print("=== 1) ctext 目录页 ===")
html = get("https://ctext.org/xi-you-ji")
print("len:", len(html))
# 找所有章节链接
for m in re.finditer(r'href="([^"]+)"[^>]*>([^<]+)</a>', html):
    txt = m.group(2)
    href = m.group(1)
    if "xi-you-ji" in href or "西游记" in txt or "回" in txt[:3]:
        print(repr(txt[:40]), "=>", href[:90])
