import json
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
ark = sys.argv[1] if len(sys.argv) > 1 else "btv1b9006389z"

for url in [
    "https://gallica.bnf.fr/iiif/ark:/12148/%s/manifest.json" % ark,
    "https://gallica.bnf.fr/iiif/ark:/12148/%s/info.json" % ark,
]:
    print("\n===== " + url)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        body = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except Exception as e:
        print("  FAIL", str(e)[:100])
        continue
    print("  len=%d" % len(body))
    print(body[:2500])
