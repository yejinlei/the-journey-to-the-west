import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

sites = [
    "web.archive.org",
    "ia801.us.archive.org",
    "openlibrary.org",
    "books.google.com",
    "www.googleapis.com",
    "catalog.hathitrust.org",
    "babel.hathitrust.org",
    "www.nlc.cn",
    "read.nlc.cn",
    "ids.lib.harvard.edu",
    "collections.library.harvard.edu",
    "dl.ndl.go.jp",
    "cadal.edu.cn",
    "shuge.org",
    "new.shuge.org",
    "www.shuge.org",
    "www.guoxuedashi.net",
    "www.zwbk.org",
    "ctext.org",
    "zh.wikisource.org",
]

for s in sites:
    try:
        req = urllib.request.Request("https://" + s + "/", headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=8)
        print("OK  ", s, r.status)
    except Exception as e:
        msg = str(e)
        if len(msg) > 55:
            msg = msg[:55]
        print("FAIL", s, type(e).__name__, msg)
