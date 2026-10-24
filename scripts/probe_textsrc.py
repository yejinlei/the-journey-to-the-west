import re
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

URLS = [
    ("guoxue123-hpxyj", "http://www.guoxue123.com/xiaosuo/jd/hpxyj/001.htm"),
    ("guoxue123-home", "http://www.guoxue123.com/"),
    ("newdu-zhengzhi", "http://ab.newdu.com/book/mbook.php?bid=16970"),
]


def strip_tags(s):
    s = re.sub(r"(?s)<script.*?</script>", "", s)
    s = re.sub(r"(?s)<style.*?</style>", "", s)
    return re.sub(r"<[^>]+>", "", s).strip()


for name, url in URLS:
    print("\n===== %s" % name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=25)
        raw = r.read()
    except Exception as e:
        print("  FAIL", type(e).__name__, str(e)[:90])
        continue
    for enc in ("utf-8", "gb18030", "gbk"):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            text = raw.decode("utf-8", "replace")
    print("  status=%s len=%d" % (r.status, len(text)))
    t = re.search(r"<title>(.*?)</title>", text, re.S)
    print("  title: %s" % (t.group(1).strip()[:70] if t else "?"))
    body = strip_tags(text)
    body = re.sub(r"\s+", " ", body)
    print("  正文样例: %s" % body[:300])
