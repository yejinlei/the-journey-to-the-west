#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量全量下载 Gallica 上已定位的《西游记》各册。

断点续传：已存在的页自动跳过，可随时中断后重跑。
用法：
  py -3 scripts/fetch_all_gallica.py
"""
import argparse
import subprocess
import sys
import time

BOOKS = [
    ("btv1b9006389z", "李评本_Gallica4031"),
    ("btv1b9006390m", "李评本_Gallica4032"),
    ("btv1b9006356k", "李评本_Gallica4033"),
    ("btv1b90063570", "李评本_Gallica4034"),
    ("btv1b9006388j", "李评本_Gallica4035"),
    ("btv1b9006354r", "大奇书本_Gallica4040"),
    ("btv1b90063555", "大奇书本_Gallica4041"),
    ("btv1b9006352x", "大奇书本_Gallica4042"),
    ("btv1b9006353b", "大奇书本_Gallica4043"),
    ("btv1b9006569w", "新刻全像批评西游记"),
]

SIZE = "2400,"
WORKERS = 6

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ap = argparse.ArgumentParser()
ap.add_argument("--start", type=int, default=1, help="起始册序号（1-based，含）")
ap.add_argument("--end", type=int, default=len(BOOKS), help="结束册序号（1-based，含）")
ap.add_argument("--workers", type=int, default=WORKERS,
                help="并发数；被限流后恢复时建议降到 3")
ap.add_argument("--proxy", help="http 代理，如 127.0.0.1:7890；用于绕开 IP 封禁")
args = ap.parse_args()

todo = BOOKS[args.start - 1:args.end]

t0 = time.time()
for i, (ark, edition) in enumerate(todo, args.start):
    print("[%d/%d] ==== %s (%s) ====" % (i, len(BOOKS), edition, ark), flush=True)
    cmd = [sys.executable, "scripts/gallica_download.py",
           "--ark", ark, "--edition", edition,
           "--size", SIZE, "--workers", str(args.workers)]
    if args.proxy:
        cmd += ["--proxy", args.proxy]
    # 单册 265-364 页，实测约 2-3 小时，超时需远大于此
    try:
        subprocess.run(cmd, timeout=86400)
    except subprocess.TimeoutExpired:
        print("   超时（24h），继续下一册", flush=True)
    print("   累计用时 %.0f 分钟" % ((time.time() - t0) / 60), flush=True)

print("全部册处理完毕，用时 %.1f 分钟" % ((time.time() - t0) / 60), flush=True)
