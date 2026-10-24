#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从书格（shuge.org）下载书页原图。

用法：
  py -3 scripts/shuge_download.py --url <书格 view 页> --edition 李评本
  py -3 scripts/shuge_download.py --url <...> --edition 证道本 --out book/scans
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.shuge.org/"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def strip_size(u):
    """去掉 WordPress 生成的 -1000x857 之类尺寸后缀，还原原图地址。"""
    return re.sub(r"-\d+x\d+(?=\.jpg$)", "", u)


def prefix_of(u):
    m = re.search(r"/([a-zA-Z0-9_\-]+?)(\d+)\.jpg$", u)
    return m.group(1) if m else None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--out", default="book/scans")
    ap.add_argument("--min-count", type=int, default=2,
                    help="同一前缀至少出现次数，用于排除单张推荐缩略图")
    args = ap.parse_args()

    out_dir = Path(args.out) / args.edition
    out_dir.mkdir(parents=True, exist_ok=True)

    html = fetch(args.url).decode("utf-8", "replace")
    cands = re.findall(r'(https://(?:www|cdn)\.shuge\.org/(?:wp-content/)?uploads/[^\s"\']+?\.jpg)', html)

    # 原图优先，缩略图兜底
    sized = {}
    for c in cands:
        o = strip_size(c)
        sized.setdefault(o, c)

    cnt = Counter()
    for o in sized:
        p = prefix_of(o)
        if p:
            cnt[p] += 1

    keep = [o for o in sized if cnt.get(prefix_of(o), 0) >= args.min_count]
    keep.sort()

    print("候选 %d，去重 %d，保留 %d（前缀出现 >= %d）" % (len(cands), len(sized), len(keep), args.min_count))
    for p, v in cnt.most_common(6):
        print("   前缀 %-50s %d" % (p, v))

    ok, fail, skipped = 0, 0, []
    for o in keep:
        name = o.rsplit("/", 1)[-1]
        dest = out_dir / name
        if dest.exists() and dest.stat().st_size > 0:
            ok += 1
            continue
        got = False
        for u in (o, sized[o]):
            try:
                data = fetch(u, timeout=90)
                dest.write_bytes(data)
                print("   %-62s %8d B" % (name, len(data)))
                got = True
                ok += 1
                break
            except Exception as e:
                last = str(e)
        if not got:
            fail += 1
            skipped.append(name)
        time.sleep(0.25)

    manifest = {
        "edition": args.edition,
        "source_page": args.url,
        "site": "shuge.org",
        "downloaded": ok,
        "failed": fail,
        "skipped": skipped,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n完成: 成功 %d，失败 %d -> %s" % (ok, fail, out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
