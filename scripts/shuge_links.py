import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
url = sys.argv[1]
req = urllib.request.Request(url, headers={"User-Agent": UA})
html = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")

print("--- links to shuge image servers / readers ---")
n = 0
for m in re.finditer(r'["\']([^"\']*(?:s\.shuge\.org|hanjihebi|old\.shuge\.org|viewer|reader|zoom)[^"\']*)["\']', html, re.I):
    print("  ", m.group(1)[:180])
    n += 1
    if n > 30:
        break

print("\n--- anchors with text ---")
n = 0
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
    href, txt = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
    if not txt or len(txt) > 40:
        continue
    if re.search(r"(下载|全本|阅读|在线|书格|盘|drive|download)", txt):
        print("  %-40s %s" % (txt, href[:130]))
        n += 1
        if n > 40:
            break
