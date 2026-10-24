# -*- coding: utf-8 -*-
"""抓取维基文库《西游记》100 回正文"""
import json
import sys
import time
import urllib.request
import urllib.error

API = "https://zh.wikisource.org/w/api.php"
UA = "MoeProjectBot/1.0 (research; contact: dev@t480.local)"


def api_get(params: dict, retries: int = 3, timeout: int = 25) -> dict:
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"{API}?{qs}"
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  [retry {i+1}/{retries}] {url[:80]}... {e}", file=sys.stderr)
            time.sleep(2 + i * 3)
    raise RuntimeError(f"fail {url}")


if __name__ == "__main__":
    # 查子页列表：西游记/第xxx回
    d = api_get({
        "action": "query", "list": "allpages",
        "apprefix": "西游记/第", "aplimit": 500, "format": "json", "formatversion": 2,
    })
    pages = [p["title"] for p in d["query"]["allpages"]]
    print(f"找到 {len(pages)} 个子页")
    print(pages[:5], "...", pages[-3:])

    # 拿前 3 回看看内容结构
    for t in pages[:3]:
        d = api_get({
            "action": "query", "prop": "revisions",
            "titles": t, "rvprop": "content", "format": "json", "formatversion": 2,
        })
        p = d["query"]["pages"][0]
        content = p.get("revisions", [{}])[0].get("content", "")
        print(f"\n=== {t} (len={len(content)}) ===")
        print(content[:800])
