import re
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

QUERIES = [
    "西游记", "西游真诠", "新说西游记", "西游原旨", "通易西游正旨",
    "西游记评注", "西游记记", "世德堂", "西游证道书", "西游",
    "唐三藏西游释厄传", "西游释厄传", "唐僧西游记", "新说西游记图像",
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


found = {}
for q in QUERIES:
    url = "https://www.shuge.org/?" + urllib.parse.urlencode({"s": q})
    try:
        html = get(url)
    except Exception as e:
        print("FAIL", q, str(e)[:60])
        continue

    titles = {}
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href, txt = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if txt and len(txt) < 90:
            titles.setdefault(href, txt)

    n = 0
    for m in re.finditer(r'https://www\.shuge\.org/(ebook|view)/([a-z0-9_\-]+)/', html):
        kind, slug = m.group(1), m.group(2)
        key = (kind, slug)
        if key in found:
            continue
        full = "https://www.shuge.org/%s/%s/" % (kind, slug)
        found[key] = (titles.get(full, ""), q)
        n += 1
    print("[%s] 新增 %d（累计 %d）" % (q, n, len(found)))

print("\n=== 全部条目 %d ===" % len(found))
for (kind, slug), (title, q) in sorted(found.items()):
    print("  [%s] %-52s %s" % (kind, slug, title[:40]))
