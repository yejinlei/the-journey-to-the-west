import re
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

CANDIDATES = [
    ("home", "https://guji.nlc.cn/"),
    ("home2", "http://guji.nlc.cn/"),
    ("search-kw", "https://guji.nlc.cn/search?" + urllib.parse.urlencode({"keyword": "西游记"})),
    ("search-q", "https://guji.nlc.cn/search?" + urllib.parse.urlencode({"q": "西游记"})),
    ("api", "https://guji.nlc.cn/api/search?" + urllib.parse.urlencode({"keyword": "西游记"})),
    ("waseda", "https://www.wul.waseda.ac.jp/kotenseki/?" + urllib.parse.urlencode({"s": "西遊記"})),
    ("waseda-home", "https://www.wul.waseda.ac.jp/kotenseki/"),
]

for name, url in CANDIDATES:
    print("\n===== %s" % name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=25)
        body = r.read()
        try:
            text = body.decode("utf-8", "replace")
        except Exception:
            text = body.decode("gbk", "replace")
        print("  status=%s len=%d" % (r.status, len(text)))
    except Exception as e:
        print("  FAIL", type(e).__name__, str(e)[:90])
        continue

    t = re.search(r"<title>(.*?)</title>", text, re.S)
    print("  title: %s" % (t.group(1).strip()[:80] if t else "?"))

    forms = re.findall(r'<form[^>]+action="([^"]+)"', text)
    if forms:
        print("  forms: %s" % forms[:5])

    hits = re.findall(r'(?:href|action)="([^"]*(?:search|Search)[^"]*)"', text)
    if hits:
        print("  search links: %s" % list(dict.fromkeys(hits))[:5])

    js_api = re.findall(r'["\'](/[a-zA-Z0-9_\-/]*(?:api|search)[a-zA-Z0-9_\-/]*)["\']', text)
    if js_api:
        print("  api-ish: %s" % list(dict.fromkeys(js_api))[:8])
