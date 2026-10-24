import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

TARGETS = [
    ("old.shuge.org", "https://old.shuge.org/?" + urllib.parse.urlencode({"s": "西遊記"})),
    ("old.shuge.org2", "https://old.shuge.org/?" + urllib.parse.urlencode({"s": "西游記"})),
]


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


for name, url in TARGETS:
    print("\n===== %s =====" % name)
    try:
        html = get(url)
    except Exception as e:
        print("  FAIL", str(e)[:80])
        continue
    print("  len =", len(html))

    links = set()
    for m in re.finditer(r'href="([^"]+)"', html):
        href = m.group(1)
        if re.search(r"(xi_?you|西遊|西游|xiyou)", href, re.I):
            links.add(href)
    for m in re.finditer(r'href="(https?://old\.shuge\.org/ebooks/[^"]+)"', html):
        links.add(m.group(1))

    titles = {}
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href, txt = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if txt and len(txt) < 80:
            titles.setdefault(href, txt)

    n = 0
    for l in sorted(links):
        t = titles.get(l, "")
        print("   %s" % l[:120])
        if t:
            print("        %s" % t)
        n += 1
        if n > 40:
            break
