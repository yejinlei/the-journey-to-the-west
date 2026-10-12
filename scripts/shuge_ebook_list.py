import re
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

# 书格旧版 ebook 列表分页
PAGES = [
    "https://www.shuge.org/ebook/",
    "https://www.shuge.org/ebook/page/2/",
    "https://www.shuge.org/ebook/page/3/",
    "https://old.shuge.org/ebooks/",
    "https://old.shuge.org/ebooks/page/2/",
    "https://old.shuge.org/ebooks/page/3/",
]

slugs = {}
for p in PAGES:
    try:
        req = urllib.request.Request(p, headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        print("FAIL", p, str(e)[:60])
        continue
    found = set(re.findall(r'shuge\.org/ebook[s]?/([a-z0-9_\-/]+)/', html))
    print("%-45s 条目 %d" % (p, len(found)))
    for s in found:
        if re.search(r"(xi-?you|xiyou|you-ji)", s, re.I):
            slugs.setdefault(s, p)

print("\n=== 与《西游记》相关的 ebook 条目 ===")
for s, p in sorted(slugs.items()):
    print("  %-55s (%s)" % (s, p))
if not slugs:
    print("  (未发现)")
