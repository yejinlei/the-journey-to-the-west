import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

url = sys.argv[1]
req = urllib.request.Request(url, headers={"User-Agent": UA})
html = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")

t = re.search(r"<title>(.*?)</title>", html, re.S)
print("title =", t.group(1).strip() if t else "?")

# 书页图特征：wp-content/uploads/<year>/<mm>/<slug><n>[-WxH].jpg
cands = re.findall(r'(https://www\.shuge\.org/wp-content/uploads/[^\s"\']+?\.jpg)', html)

# 去掉 WordPress 尺寸后缀，还原原图
def original(u):
    return re.sub(r"-\d+x\d+(?=\.jpg$)", "", u)

orig = []
seen = set()
for c in cands:
    o = original(c)
    if o in seen:
        continue
    seen.add(o)
    orig.append(o)

print("候选图片 %d 个，去重后原图 %d 个" % (len(cands), len(orig)))

from collections import Counter
stem = Counter()
for o in orig:
    m = re.search(r"/([a-z0-9_]+?)(\d+)\.jpg$", o)
    if m:
        stem[m.group(1)] += 1

print("\n前缀统计（前 10）:")
for k, v in stem.most_common(10):
    print("   %-60s %d" % (k, v))

print("\n示例（前 8 个原图 URL）:")
for o in orig[:8]:
    print("   " + o)
