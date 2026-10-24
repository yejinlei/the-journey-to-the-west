#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gallica 403 限流后自动恢复下载。

持续探测 manifest 是否恢复；一旦恢复，三片并行补下所有缺失页。
可长期后台运行：
  Start-Process py -ArgumentList "-3","scripts\\resume_gallica.py" -RedirectStandardOutput "book\\scans\\_resume.log" -WindowStyle Hidden
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANS = ROOT / "book" / "scans"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
PROBE_ARK = "btv1b9006390m"
PROBE_URL = "https://gallica.bnf.fr/iiif/ark:/12148/%s/manifest.json" % PROBE_ARK

# 三片分片，与 fetch_all_gallica.py 的 --start/--end 对应
SLICES = [(1, 4), (5, 7), (8, 10)]
WAIT_SECONDS = 600          # 每次探测间隔
MAX_HOURS = 720             # 30 天，避免长时间封禁期间脚本自己退出
PROXY = None                # 由 --proxy 设置

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def alive():
    try:
        req = urllib.request.Request(PROBE_URL, headers={"User-Agent": UA})
        body = urllib.request.urlopen(req, timeout=40).read()
        return len(body) > 100
    except Exception as e:
        print("  探测失败: %s" % e, flush=True)
        return False


def missing_summary():
    """返回 (缺页册数, 缺页总数)。"""
    dirs = [d for d in SCANS.iterdir() if d.is_dir() and (d / "manifest.json").exists()]
    lack_dirs = 0
    lack_pages = 0
    for d in dirs:
        try:
            m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
            total = m.get("total_pages") or 0
        except Exception:
            continue
        got = len(list(d.glob("*.jpg")))
        if total and got < total:
            lack_dirs += 1
            lack_pages += total - got
    return lack_dirs, lack_pages


def run_slices():
    procs = []
    for a, b in SLICES:
        log = SCANS / ("_fetch_%s.log" % {1: "a", 5: "b", 8: "c"}[a])
        err = SCANS / ("_fetch_%s.err" % {1: "a", 5: "b", 8: "c"}[a])
        f = open(log, "w", encoding="utf-8")
        e = open(err, "w", encoding="utf-8")
        # 限流刚恢复时用低并发，避免再次触发封禁
        cmd = [sys.executable, "scripts/fetch_all_gallica.py",
               "--start", str(a), "--end", str(b), "--workers", "3"]
        if PROXY:
            cmd += ["--proxy", PROXY]
        procs.append(subprocess.Popen(cmd, cwd=str(ROOT), stdout=f, stderr=e))
        print("  启动分片 %d-%d" % (a, b), flush=True)
    for p in procs:
        p.wait()
    print("  三片均结束", flush=True)


def main():
    global WAIT_SECONDS, PROXY
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=WAIT_SECONDS,
                    help="探测间隔秒数，默认 600")
    ap.add_argument("--proxy", help="http 代理，如 127.0.0.1:8001")
    a = ap.parse_args()
    WAIT_SECONDS = a.interval
    PROXY = a.proxy

    t0 = time.time()
    print("resume 启动，探测间隔 %d 秒，最长 %d 小时%s"
          % (WAIT_SECONDS, MAX_HOURS, ("，代理 %s" % PROXY) if PROXY else ""), flush=True)
    while True:
        d, p = missing_summary()
        print("%s  缺失：%d 册 / %d 页" % (time.strftime("%H:%M:%S"), d, p), flush=True)
        if p == 0:
            print("无缺失，全部下载完成。", flush=True)
            return 0

        if not alive():
            elapsed = (time.time() - t0) / 3600
            if elapsed > MAX_HOURS:
                print("超过 %d 小时仍未恢复，退出。" % MAX_HOURS, flush=True)
                return 2
            print("  仍被限流，%d 秒后重试（已等待 %.1f 小时）" % (WAIT_SECONDS, elapsed), flush=True)
            time.sleep(WAIT_SECONDS)
            continue

        print("  Gallica 已恢复，开始补下", flush=True)
        run_slices()
        time.sleep(60)


if __name__ == "__main__":
    sys.exit(main())
