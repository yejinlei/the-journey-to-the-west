import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

QUERIES = [
    "西游记",
    "西游证道书",
    "新说西游记",
    "西游真诠",
    "李卓吾",
    "西游原旨",
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


for q in QUERIES:
    url = "https://www.shuge.org/?" + urllib.parse.urlencode({"s": q})
    print("\n=== " + q + " ===")
    try:
        html = get(url)
    except Exception as e:
        print("  FAIL", str(e)[:80])
        continue

    items = []
    for m in re.finditer(
        r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        items.append((m.group(1), strip_tags(m.group(2))))

    if not items:
        for m in re.finditer(r'href="(https://www\.shuge\.org/\w+/[^"]+)"[^>]*>([^<]{4,60})</a>', html):
            items.append((m.group(1), m.group(2).strip()))

    seen = set()
    n = 0
    for link, title in items:
        if link in seen:
            continue
        seen.add(link)
        if not title:
            continue
        print("  " + title + "\n      " + link)
        n += 1
        if n >= 12:
            break
    if n == 0:
        print("  (未解析到结果，页面长度 %d)" % len(html))
