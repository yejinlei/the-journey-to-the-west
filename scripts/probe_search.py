import re
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

Q = urllib.parse.quote("西遊記")
Q2 = urllib.parse.quote("xiyouji")

URLS = [
    ("NDL-html", "https://dl.ndl.go.jp/search?cs=bib&keyword=" + Q),
    ("utokyo", "https://da.dl.itc.u-tokyo.ac.jp/portal/search?keyword=" + Q),
    ("keio", "https://dcollections.lib.keio.ac.jp/search?query=" + Q),
    ("ubc", "https://open.library.ubc.ca/search?q=" + Q2),
    ("berkeley", "https://digicoll.lib.berkeley.edu/search?search_api_fulltext=" + Q2),
    ("bodleian", "https://digital.bodleian.ox.ac.uk/search/?q=" + Q2),
    ("gallica-sru",
     "https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&maximumRecords=20&query="
     + urllib.parse.quote('gallica all "xi you ji"')),
    ("npm", "https://digitalarchive.npm.gov.tw/Search/Index?keyword=" + Q),
]

for name, url in URLS:
    print("\n===== %s =====" % name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=30)
        body = r.read().decode("utf-8", "replace")
        print("  status=%s len=%d" % (r.status, len(body)))
    except Exception as e:
        print("  FAIL", type(e).__name__, str(e)[:90])
        continue

    hits = []
    # 抓取含关键词的链接
    for m in re.finditer(r'href="([^"]+)"', body):
        href = m.group(1)
        if re.search(r"(xi_?you|xiyou)", href, re.I):
            hits.append(href)
    # SRU / XML 标题
    for m in re.finditer(r"<dc:title[^>]*>(.*?)</dc:title>", body, re.S):
        hits.append("TITLE: " + re.sub(r"<[^>]+>", "", m.group(1)).strip())
    for m in re.finditer(r"<title>(.*?)</title>", body[:200000], re.S):
        t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if t and t not in ("Search", "Home"):
            hits.append("TITLE: " + t)

    seen = set()
    n = 0
    for h in hits:
        if h in seen:
            continue
        seen.add(h)
        print("   " + h[:140])
        n += 1
        if n >= 15:
            break
    if n == 0:
        print("   (无命中)")
