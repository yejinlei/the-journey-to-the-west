import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

url = sys.argv[1] if len(sys.argv) > 1 else "https://www.shuge.org/view/li_zhuowu_xian_sheng_pi_ping_xi_you_ji/"

req = urllib.request.Request(url, headers={"User-Agent": UA})
html = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")

print("len =", len(html))

t = re.search(r"<title>(.*?)</title>", html, re.S)
print("title =", t.group(1).strip() if t else "?")

print("\n--- download-ish links ---")
n = 0
for m in re.finditer(r'href="([^"]+)"', html):
    u = m.group(1)
    if re.search(r"(download|\.zip|\.pdf|\.rar|pan\.baidu|aliyundrive|lanzou|weiyun|drive\.google)", u, re.I):
        print("  ", u)
        n += 1
        if n > 25:
            break

print("\n--- iiif / manifest ---")
n = 0
for m in re.finditer(r'["\']([^"\']*(?:iiif|manifest|info\.json)[^"\']*)["\']', html, re.I):
    print("  ", m.group(1)[:160])
    n += 1
    if n > 15:
        break

print("\n--- image src ---")
n = 0
for m in re.finditer(r'(?:src|data-src)="([^"]+\.(?:jpg|jpeg|png|tif|jp2))"', html, re.I):
    print("  ", m.group(1)[:160])
    n += 1
    if n > 10:
        break

print("\n--- other hosts ---")
hosts = set(re.findall(r'https?://([a-z0-9\.\-]+)', html))
interesting = [h for h in hosts if h not in ("www.shuge.org", "shuge.org") and
               not re.search(r"(w3\.org|schema\.org|wordpress|gravatar|google|facebook|twitter|jquery|cdn)", h, re.I)]
for h in sorted(interesting)[:40]:
    print("  ", h)
