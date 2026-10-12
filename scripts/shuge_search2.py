import re
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

QUERIES = [
    "西游记", "世德堂", "西游", "唐三藏", "释厄传", "真诠", "新说",
    "原旨", "正旨", "含晶子", "西游记记", "全像西游记", "批评西游记",
    "官板大字", "西游传",
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
    for m in re.finditer(r'https://www\.shuge\.org/view/([a-z0-9_\-]+)/', html):
        slug = m.group(1)
        if slug not in found:
            found[slug] = q
    print("queried: %-14s (累计 %d)" % (q, len(found)))

print("\n=== 全部 /view/ 条目 (%d) ===" % len(found))
for slug, q in sorted(found.items(), key=lambda x: x[1]):
    print("  %-58s  首次命中: %s" % (slug, q))
