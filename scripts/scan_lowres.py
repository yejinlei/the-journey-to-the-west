#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量扫描 book/scans 下所有 jpg 的尺寸，找出低分辨率异常项。

判据：同一目录内宽度明显低于该目录众数的文件，视为混入的低清图/预览图。
输出清单到 book/LOWRES.md。
  py -3 scripts/scan_lowres.py
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANS = ROOT / "book" / "scans"
OUT = ROOT / "book" / "LOWRES.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GALLICA_PREFIX = ("Gallica",)


def jpeg_size(path):
    with open(path, "rb") as f:
        data = f.read(100000)
    i, n = 2, len(data)
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


def main():
    report = []
    grand_bad = 0
    # 跳过 _logs、_quarantine 等下划线开头的辅助目录
    for d in sorted([x for x in SCANS.iterdir()
                     if x.is_dir() and not x.name.startswith("_")]):
        files = sorted(d.glob("*.jpg"))
        if not files:
            continue
        sizes = []
        for f in files:
            try:
                wh = jpeg_size(f)
            except Exception:
                wh = None
            sizes.append((f.name, wh))

        widths = [w for _, wh in sizes if wh for w in [wh[0]]]
        if not widths:
            continue
        mode_w = Counter(widths).most_common(1)[0][0]
        # 低于众数 90% 的视为异常
        thr = int(mode_w * 0.9)
        bad = [(n, wh) for n, wh in sizes if wh and wh[0] < thr]
        err = [(n,) for n, wh in sizes if not wh]

        report.append({
            "dir": d.name,
            "count": len(files),
            "mode": "%dx%d" % (mode_w, max(h for _, wh in sizes if wh for h in [wh[1]])),
            "min": min(widths),
            "bad": bad,
            "err": err,
            # 整目录都低：众数本身就达不到 1600px，此类没有"异常项"可言
            "low": mode_w < 1600,
        })
        grand_bad += len(bad) + len(err)

    lines = ["# 低分辨率文件清单\n",
             "自动生成：`py -3 scripts/scan_lowres.py`\n",
             "判据：同目录内宽度低于该目录众数 90% 的文件。\n",
             "\n| 目录 | 张数 | 主流尺寸 | 最窄 | 异常数 |",
             "|---|---|---|---|---|"]
    total_img = 0
    for r in report:
        total_img += r["count"]
        lines.append("| `%s` | %d | %s | %d | %d |"
                     % (r["dir"], r["count"], r["mode"], r["min"],
                        len(r["bad"]) + len(r["err"])))
    lines.append("\n合计图像 %d 张，异常 %d 张。\n" % (total_img, grand_bad))

    low_dirs = [r for r in report if r["low"]]
    if low_dirs:
        lines.append("\n## 整目录低分辨率（整体偏低，需另找来源）\n")
        lines.append("\n| 目录 | 张数 | 尺寸 | 说明 |")
        lines.append("|---|---|---|---|")
        for r in low_dirs:
            lines.append("| `%s` | %d | %s | 全目录低于 1600px，提取批注基本不可行 |"
                         % (r["dir"], r["count"], r["mode"]))
        lines.append("")

    for r in report:
        if not (r["bad"] or r["err"]):
            continue
        is_gallica = any(p in r["dir"] for p in GALLICA_PREFIX)
        lines.append("\n## `%s`（主流 %s）\n" % (r["dir"], r["mode"]))
        if is_gallica:
            lines.append("Gallica 册：标准应为 2400px 宽，以下可直接删除后由断点续传补下。\n")
        else:
            lines.append("书格来源：原图尺寸本就不统一，需回源站确认是否有更大的版本。\n")
        lines.append("\n```")
        for n, wh in r["bad"][:40]:
            lines.append("%s    %s" % (n, "%dx%d" % wh if wh else "?"))
        for (n,) in r["err"][:10]:
            lines.append("%s    读取失败" % n)
        if len(r["bad"]) > 40:
            lines.append("... 其余 %d 张省略" % (len(r["bad"]) - 40))
        lines.append("```")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("已写入 %s" % OUT)
    print("合计 %d 张，异常 %d 张" % (total_img, grand_bad))
    for r in report:
        if r["bad"] or r["err"]:
            print("  %-26s 主流 %-12s 异常 %d"
                  % (r["dir"], r["mode"], len(r["bad"]) + len(r["err"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
