#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从书格存储（OpenList）分块并发下载大文件，支持断点续传。

用法：
  py -3 scripts/download_shuge_pdf.py
  py -3 scripts/download_shuge_pdf.py --url <直链> --out <路径> --workers 8
"""
import argparse
import math
import os
import ssl
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

DEFAULT_URL = "https://bw.shuge.org/sd/iOXveWd1/"
DEFAULT_OUT = "book/scans/世德堂本/新刻出像官板大字西游记.世德堂本.灰度胶片.pdf"
CHUNK = 8 * 1024 * 1024      # 每块 8MB

ap = argparse.ArgumentParser()
ap.add_argument("--url", default=DEFAULT_URL)
ap.add_argument("--out", default=DEFAULT_OUT)
ap.add_argument("--workers", type=int, default=8)
ap.add_argument("--chunk", type=int, default=CHUNK)
args = ap.parse_args()

OUT = Path(args.out)
PARTS = OUT.parent / (OUT.stem + ".parts")
lock = threading.Lock()
done = [0]
total_bytes = [0]


def head_size():
    req = urllib.request.Request(args.url, headers={"User-Agent": UA}, method="GET")
    r = urllib.request.urlopen(req, timeout=40, context=CTX)
    return int(r.headers.get("Content-Length", 0)), r.headers.get("Accept-Ranges", "")


def fetch_range(start, end):
    h = {"User-Agent": UA, "Range": "bytes=%d-%d" % (start, end)}
    req = urllib.request.Request(args.url, headers=h)
    r = urllib.request.urlopen(req, timeout=120, context=CTX)
    return r.read()


def download_chunk(idx, start, end):
    p = PARTS / ("part_%05d" % idx)
    expect = end - start + 1
    if p.exists() and p.stat().st_size == expect:
        with lock:
            done[0] += 1
            total_bytes[0] += expect
        return True
    for attempt in range(1, 6):
        try:
            data = fetch_range(start, end)
            if len(data) != expect:
                raise IOError("长度不符 %d != %d" % (len(data), expect))
            tmp = p.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(p)
            with lock:
                done[0] += 1
                total_bytes[0] += len(data)
            return True
        except Exception as e:
            print("   块 %d 第 %d 次失败: %s" % (idx, attempt, str(e)[:60]), flush=True)
            time.sleep(3 * attempt)
    return False


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PARTS.mkdir(parents=True, exist_ok=True)

    size, ranges = head_size()
    if not size:
        print("无法获取文件大小")
        return 1
    print("文件: %s" % OUT.name)
    print("大小: %.2f GB (%d 字节)" % (size / 1073741824, size))
    print("Accept-Ranges: %s" % (ranges or "无"))
    if "bytes" not in (ranges or ""):
        print("不支持断点续传，改为单线程")
    n = math.ceil(size / args.chunk)
    print("分块: %d 块 x %.0f MB，并发 %d" % (n, args.chunk / 1048576, args.workers))

    tasks = []
    for i in range(n):
        s = i * args.chunk
        e = min(s + args.chunk - 1, size - 1)
        tasks.append((i, s, e))

    t0 = time.time()
    fails = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_chunk, i, s, e): i for i, s, e in tasks}
        for f in futs:
            pass
        # 等待并统计
        for fut, i in list(futs.items()):
            try:
                if not fut.result():
                    fails.append(i)
            except Exception as ex2:
                fails.append(i)
                print("  块 %d 异常 %s" % (i, str(ex2)[:50]))
            if done[0] % 20 == 0:
                el = time.time() - t0
                spd = total_bytes[0] / 1048576 / el if el > 0 else 0
                print("  进度 %d/%d  已下 %.0f MB  %.1f MB/s"
                      % (done[0], n, total_bytes[0] / 1048576, spd), flush=True)

    print("完成 %d/%d 块，失败 %d 块" % (done[0], n, len(fails)))
    if fails:
        print("失败块序号: %s" % fails[:20])
        return 2

    print("合并中...")
    with open(OUT, "wb") as out:
        for i in range(n):
            p = PARTS / ("part_%05d" % i)
            out.write(p.read_bytes())
    got = OUT.stat().st_size
    print("合并完成: %s  %.2f GB" % (OUT, got / 1073741824))
    if got != size:
        print("!! 大小不符 %d != %d" % (got, size))
        return 3
    for p in PARTS.glob("part_*"):
        p.unlink()
    PARTS.rmdir()
    print("校验通过，用时 %.1f 分钟" % ((time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    sys.exit(main())
