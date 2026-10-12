#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查已下载图像的实际分辨率（纯标准库，不解码像素）。

按版本采样，输出像素尺寸，用于判断眉批/夹批是否可 OCR。
  py -3 scripts/check_resolution.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANS = ROOT / "book" / "scans"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def jpeg_size(path):
    """从 JPEG 头部解析宽高。"""
    with open(path, "rb") as f:
        data = f.read(200000)
    i = 2
    n = len(data)
    while i < n - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        m = data[i + 1]
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7 or m == 0x01:
            i += 2
            continue
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6,
                 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h
        if i + 4 > n:
            return None
        seg = int.from_bytes(data[i + 2:i + 4], "big")
        if seg <= 0:
            return None
        i += 2 + seg
    return None


def sample(files, k=3):
    if not files:
        return []
    idxs = [0]
    if len(files) > 1:
        idxs.append(len(files) // 2)
    if len(files) > 2:
        idxs.append(len(files) - 1)
    return idxs[:k]


def main():
    dirs = sorted([d for d in SCANS.iterdir() if d.is_dir()])
    print("%-26s %-8s %s" % ("目录", "张数", "采样尺寸 (宽x高)"))
    print("-" * 76)
    any_small = []
    for d in dirs:
        files = sorted(d.glob("*.jpg"))
        if not files:
            continue
        sizes = []
        for i in sample(files):
            try:
                wh = jpeg_size(files[i])
                if wh:
                    sizes.append("%dx%d" % wh)
            except Exception as e:
                sizes.append("ERR:%s" % e)
        line = "%-26s %-8d %s" % (d.name, len(files), ", ".join(sizes))
        print(line)
        # 记录明显偏小的：判断阈值为宽 < 1600
        for s in sizes:
            if s.startswith("ERR"):
                continue
            try:
                w = int(s.split("x")[0])
                if w < 1600:
                    any_small.append((d.name, s))
            except ValueError:
                pass
    print("-" * 76)
    if any_small:
        print("分辨率偏低（宽 < 1600px）的样本：")
        for name, s in any_small:
            print("  %-26s %s" % (name, s))
    else:
        print("所有采样均 >= 1600px 宽。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
