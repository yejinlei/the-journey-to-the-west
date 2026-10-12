#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Gallica（法国国家图书馆）按 IIIF 下载古籍书页图像。

用法：
  # 先看该册有多少页
  py -3 scripts/gallica_download.py --ark btv1b9006389z --info

  # 下载（可限制页数、指定 IIIF 尺寸）
  py -3 scripts/gallica_download.py --ark btv1b9006389z --edition 李评本_Gallica_4031 --max-pages 5
  py -3 scripts/gallica_download.py --ark btv1b9006389z --edition 李评本_Gallica_4031 --size 2400,
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROXY = None   # 由 --proxy 设置，形如 127.0.0.1:7890 或 http://127.0.0.1:7890
_opener = None


def build_opener(force=False):
    """构造 opener：优先 --proxy，其次 HTTP(S)_PROXY 环境变量。

    仅支持 http/https 代理；socks5 需另装 PySocks 并自行适配。
    """
    global _opener
    if _opener is not None and not force:
        return _opener
    d = {}
    if PROXY:
        p = PROXY if "://" in PROXY else "http://" + PROXY
        d["https"] = p
        d["http"] = p
    https_p = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    http_p = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if https_p:
        d["https"] = https_p
    if http_p:
        d["http"] = http_p
    handlers = []
    if d:
        print("   使用代理: %s" % d, flush=True)
        handlers.append(urllib.request.ProxyHandler(d))
    _opener = urllib.request.build_opener(*handlers)
    return _opener


def fetch(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return build_opener().open(req, timeout=timeout).read()


def collect_ids(node, out):
    """递归收集 IIIF image service 的 @id / id。"""
    if isinstance(node, dict):
        for k in ("@id", "id"):
            v = node.get(k)
            if isinstance(v, str) and "/iiif/ark:" in v:
                out.add(v)
        for v in node.values():
            collect_ids(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_ids(v, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ark", required=True, help="如 btv1b9006389z")
    ap.add_argument("--edition", help="输出子目录名（book/scans 下）")
    ap.add_argument("--out", default="book/scans")
    ap.add_argument("--size", default="full", help="IIIF size，如 full / 2400, / ,3000")
    ap.add_argument("--max-pages", type=int, default=0, help="0=全部")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4, help="并发下载线程数")
    ap.add_argument("--retries", type=int, default=3, help="单页失败重试次数")
    ap.add_argument("--proxy", help="http 代理，如 127.0.0.1:7890")
    ap.add_argument("--info", action="store_true", help="只查看页数信息")
    args = ap.parse_args()

    global PROXY
    PROXY = args.proxy
    build_opener(force=True)

    manifest_url = "https://gallica.bnf.fr/iiif/ark:/12148/%s/manifest.json" % args.ark
    print("manifest: " + manifest_url)
    # manifest 请求失败会导致整册被跳过，必须重试
    raw = None
    for attempt in range(1, 6):
        try:
            raw = fetch(manifest_url, timeout=90)
            break
        except Exception as e:
            print("   manifest 请求失败(%d/5): %s" % (attempt, e), flush=True)
            time.sleep(15 * attempt)
    if raw is None:
        print("   manifest 连续失败，放弃该册", flush=True)
        return 1
    man = json.loads(raw.decode("utf-8", "replace"))

    ids = set()
    collect_ids(man, ids)

    def page_key(u):
        m = re.search(r"/f(\d+)$", u)
        return int(m.group(1)) if m else 0

    pages = sorted([i for i in ids
                    if re.search(r"/f\d+$", i) and "/canvas/" not in i], key=page_key)

    label = ""
    try:
        label = man.get("label", "")
        if isinstance(label, list) and label:
            label = label[0].get("@value", "") if isinstance(label[0], dict) else str(label[0])
    except Exception:
        pass

    print("标题: %s" % str(label)[:120])
    print("页数: %d" % len(pages))
    if args.info:
        for p in pages[:5]:
            print("   " + p)
        return 0

    if not args.edition:
        print("需指定 --edition")
        return 1

    out_dir = Path(args.out) / args.edition
    out_dir.mkdir(parents=True, exist_ok=True)

    todo = pages[args.start - 1:]
    if args.max_pages:
        todo = todo[:args.max_pages]

    print("本次下载 %d 页 -> %s" % (len(todo), out_dir))

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def dl(job):
        idx, svc = job
        url = "%s/full/%s/0/native.jpg" % (svc, args.size)
        dest = out_dir / ("p%04d.jpg" % idx)
        if dest.exists() and dest.stat().st_size > 0:
            return idx, -1
        for _ in range(args.retries):
            try:
                data = fetch(url, timeout=180)
                if len(data) < 1024:
                    raise ValueError("too small %d" % len(data))
                dest.write_bytes(data)
                return idx, len(data)
            except Exception:
                time.sleep(1.5)
        return idx, -2

    jobs = list(enumerate(todo, start=args.start))
    ok, fail, total_bytes = 0, 0, 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(dl, j) for j in jobs]
        done = 0
        for fut in as_completed(futs):
            idx, n = fut.result()
            done += 1
            if n == -2:
                fail += 1
                print("   p%04d  FAIL" % idx)
            else:
                ok += 1
                if n > 0:
                    total_bytes += n
            if done % 10 == 0 or done == len(jobs):
                print("   进度 %d/%d" % (done, len(jobs)))

    print("\n完成 %d 页，失败 %d，共 %.1f MB，用时 %.0fs"
          % (ok, fail, total_bytes / 1048576, time.time() - t0))

    meta = {
        "edition": args.edition,
        "ark": args.ark,
        "manifest": manifest_url,
        "title": str(label)[:300],
        "total_pages": len(pages),
        "downloaded": ok,
        "failed": fail,
        "iiif_size": args.size,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
