import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

SLUGS = [
    "xi-you-zhen-quan",
    "xin-shuo-xi-you-ji",
    "xi-you-yuan-zhi",
    "tong-yi-xi-you-zheng-zhi",
    "xi-you-ji-ping-zhu",
    "xi-you-ji-ji",
    "shi-de-tang-ben-xi-you-ji",
    "xi-you-zheng-dao-shu",
    "xi-you-ji",
    "xin-ke-guan-ban-da-zi-xi-you-ji",
    "xi-you-zheng-dao-da-qi-shu",
    "xi-you-ji-ji",
    "han-jing-zi-xi-you-ji-ping-zhu",
    "xin-shuo-xi-you-ji-tu-xiang",
]

for s in SLUGS:
    url = "https://www.shuge.org/ebook/%s/" % s
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=25)
        body = r.read().decode("utf-8", "replace")
        print("OK   %-40s status=%s len=%d" % (s, r.status, len(body)))
    except Exception as e:
        print("FAIL %-40s %s" % (s, str(e)[:50]))
