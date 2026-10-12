#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 book/scans，生成下载进度报告 book/DOWNLOAD-STATUS.md。

随时可运行：
  py -3 scripts/download_status.py
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCANS = ROOT / "book" / "scans"
OUT = ROOT / "book" / "DOWNLOAD-STATUS.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 版本归属：目录名 -> (汇评本编号/简称, 源, 源地址)
META = {
    "李评本_Gallica4031": ("2 李评本", "Gallica", "ark:/12148/btv1b9006389z"),
    "李评本_Gallica4032": ("2 李评本", "Gallica", "ark:/12148/btv1b9006390m"),
    "李评本_Gallica4033": ("2 李评本", "Gallica", "ark:/12148/btv1b9006356k"),
    "李评本_Gallica4034": ("2 李评本", "Gallica", "ark:/12148/btv1b90063570"),
    "李评本_Gallica4035": ("2 李评本", "Gallica", "ark:/12148/btv1b9006388j"),
    "大奇书本_Gallica4040": ("4 大奇书本", "Gallica", "ark:/12148/btv1b9006354r"),
    "大奇书本_Gallica4041": ("4 大奇书本", "Gallica", "ark:/12148/btv1b90063555"),
    "大奇书本_Gallica4042": ("4 大奇书本", "Gallica", "ark:/12148/btv1b9006352x"),
    "大奇书本_Gallica4043": ("4 大奇书本", "Gallica", "ark:/12148/btv1b9006353b"),
    "新刻全像批评西游记": ("（待辨，Chinois 4044）", "Gallica", "ark:/12148/btv1b9006569w"),
    "李评本": ("2 李评本", "书格", "https://www.shuge.org/view/li_zhuowu_xian_sheng_pi_ping_xi_you_ji/"),
    "闽斋堂本": ("3 闽斋堂本", "书格", "https://www.shuge.org/view/xin_ke_zeng_bu_pi_ping_quan_xiang_xi_you_ji/"),
    "证道本": ("4 证道本", "书格", "https://www.shuge.org/view/juan_xiang_gu_ben_xi_you_zheng_dao_shu/"),
    "杨闽斋本": ("（非评点本，参校用）", "书格", "https://www.shuge.org/view/ding_juan_jing_ben_quan_xiang_xi_you_ji/"),
    "真诠本": ("5 真诠本", "书格旧版", "https://www.shuge.org/ebook/xi-you-zhen-quan/"),
}

MISSING = [
    "1 世德堂本（世本）",
    "6 新说本 / 新图本",
    "7 原旨本",
    "8 正旨本",
    "9 含评本",
    "10 清抄本",
]


def main():
    rows = []
    total_jpg = 0
    total_mb = 0.0
    for d in sorted(SCANS.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        jpgs = list(d.glob("*.jpg"))
        mb = sum(f.stat().st_size for f in jpgs) / 1048576
        total_jpg += len(jpgs)
        total_mb += mb

        man = d / "manifest.json"
        total_pages = None
        ark = ""
        if man.exists():
            try:
                m = json.loads(man.read_text(encoding="utf-8"))
                total_pages = m.get("total_pages")
                ark = m.get("ark", "")
            except Exception:
                pass

        name, src, url = META.get(d.name, ("?", "?", "?"))
        rows.append({
            "dir": d.name,
            "edition": name,
            "src": src,
            "url": url,
            "got": len(jpgs),
            "total": total_pages,
            "mb": mb,
        })

    lines = []
    lines.append("# 下载进度\n")
    lines.append("自动生成：`py -3 scripts/download_status.py`　　"
                 "最后更新：%s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("图像合计：**%d 张 / %.1f MB**\n" % (total_jpg, total_mb))

    lines.append("\n## 各版本明细\n")
    lines.append("| 目录 | 对应版本 | 源 | 已下 / 总数 | 体积 | 状态 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        if r["total"]:
            prog = "%d / %d" % (r["got"], r["total"])
            pct = r["got"] * 100 // r["total"]
            state = "完成" if r["got"] >= r["total"] else "进行中 %d%%" % pct
        else:
            prog = "%d / ?" % r["got"]
            state = "样图（源站仅此数量）"
        lines.append("| `%s` | %s | %s | %s | %.1f MB | %s |"
                     % (r["dir"], r["edition"], r["src"], prog, r["mb"], state))

    pdfs = sorted(SCANS.rglob("*.pdf"))
    if pdfs:
        lines.append("\n## PDF 整本资源\n")
        lines.append("| 文件 | 体积 | 备注 |")
        lines.append("|---|---|---|")
        for f in pdfs:
            mb = f.stat().st_size / 1048576
            note = ""
            if "世德堂" in f.name:
                note = "汇评本底本（台湾世本），1298 页，约 300 dpi，8bit 灰度"
            lines.append("| `%s` | %.0f MB | %s |" % (f.name, mb, note))
        lines.append("")

    lines.append("\n## 尚未找到图像源的版本\n")
    for m in MISSING:
        lines.append("- %s" % m)
    lines.append("\n书格与 Gallica 均已检索穷尽（拼音 slug 逐个试过、Gallica SRU 查询 0 命中）。"
                 "剩余希望为哈佛、国图、日本各馆，当前网络不可达。\n")

    lines.append("\n## 断线后如何继续\n")
    lines.append("下载脚本具备断点续传：**已存在的页自动跳过，只补缺失页**。直接重跑即可。\n")
    lines.append("```powershell\n")
    lines.append("cd f:\\src\\The-Journey-to-the-West\n")
    lines.append("\n# 1) 先看进度\n")
    lines.append("py -3 scripts/download_status.py\n")
    lines.append("\n# 2) 续跑 Gallica 全部 10 册（单片串行，简单但慢）\n")
    lines.append("py -3 scripts/fetch_all_gallica.py\n")
    lines.append("\n# 2b) 续跑（三片并行，推荐：实测 22.5 页/分钟，失败率 0）\n")
    lines.append("$wd = 'f:\\src\\The-Journey-to-the-West'\n")
    lines.append('Start-Process py -ArgumentList "-3","scripts\\fetch_all_gallica.py","--start","1","--end","4" -WorkingDirectory $wd -RedirectStandardOutput "book\\scans\\_fetch_a.log" -WindowStyle Hidden\n')
    lines.append('Start-Process py -ArgumentList "-3","scripts\\fetch_all_gallica.py","--start","5","--end","7" -WorkingDirectory $wd -RedirectStandardOutput "book\\scans\\_fetch_b.log" -WindowStyle Hidden\n')
    lines.append('Start-Process py -ArgumentList "-3","scripts\\fetch_all_gallica.py","--start","8","--end","10" -WorkingDirectory $wd -RedirectStandardOutput "book\\scans\\_fetch_c.log" -WindowStyle Hidden\n')
    lines.append("\n# 进度日志：book/scans/_fetch_a.log、_fetch_b.log、_fetch_c.log\n")
    lines.append("\n# 2c) 若 Gallica 返回 403（整站限流，大批量下载后易触发）：\n")
    lines.append("#     自动等待解除并补下所有缺失页，每 10 分钟探测一次，最长 24 小时\n")
    lines.append('Start-Process py -ArgumentList "-3","scripts\\resume_gallica.py" -WorkingDirectory $wd -RedirectStandardOutput "book\\scans\\_resume.log" -WindowStyle Hidden\n')
    lines.append("# 分片顺序：A=4031-4034  B=4035,4040,4041  C=4042,4043,新刻全像\n")
    lines.append("\n# 3) 只续跑某一册\n")
    lines.append("py -3 scripts/gallica_download.py --ark btv1b9006390m --edition 李评本_Gallica4032 --size 2400, --workers 6\n")
    lines.append("\n# 4) 补下书格某一版本\n")
    lines.append("py -3 scripts/shuge_download.py --url https://www.shuge.org/ebook/xi-you-zhen-quan/ --edition 真诠本\n")
    lines.append("```\n")

    lines.append("\n## 过程记录（踩过的坑）\n")
    lines.append("1. **书格有两条路径、两套图床**：新版 `/view/<slug>/` 图在 `www.shuge.org/wp-content/uploads/`；"
                 "旧版 `/ebook/<slug>/` 图在 `cdn.shuge.org/uploads/`。检索 `/view/` 会漏掉旧版条目"
                 "（《西游真诠》就是这样被漏掉的）。\n")
    lines.append("2. **前缀正则要支持连字符**：旧版文件名形如 `xi-you-zhen-quan01.jpg`，"
                 "只匹配 `[a-zA-Z0-9_]` 会导致统计为 0、一张不下。\n")
    lines.append("3. **Gallica IIIF 结构**：`https://gallica.bnf.fr/iiif/ark:/12148/<ark>/manifest.json` → "
                 "`sequences[0].canvases[].images[].resource.service['@id']`，形如 `.../f1`（不是 `f1n1`），"
                 "且要排除 `.../canvas/f1`，否则页数翻倍。\n")
    lines.append("4. **分辨率上限是实测出来的**：原图 5243×4073（约 780 dpi）与 3600px 都会 `IncompleteRead` 断流，"
                 "2400px（约 360 dpi）是能稳定下完的上限。360 dpi 够看眉批，夹批吃力。\n")
    lines.append("5. **并发有效但有限**：单线程 25 秒/页，6 线程约 11 秒/页；受服务端吞吐限制，再多线程提升不大。\n")
    lines.append("6. `fetch_all_gallica.py` 的单册 subprocess 超时最初设为 3600 秒，"
                 "而单册实际需 2–3 小时，会导致每册下到约 60%% 被截断，已改为 86400 秒。\n")
    lines.append("7. **白文基底分回与汇评本不一致**：`book/text/00-baiwen/` 是人文本系，第九回不含唐僧身世；"
                 "汇评本第九至十二回用证道本分回。挂批注前必须先对齐，否则 9–12 回会错位。\n")
    lines.append("8. **李评本批注只在回末**：实测 Gallica4031（李卓吾先生批评西游记，金陵大業堂重梓），"
                 "每回结构 = 回前跨页插图 + 正文约 11 页 + 回末「分解／總批」；正文页无眉批无夹批（仅句读圈点）。"
                 "總批字体与正文同大，2400px 下清晰可读，提取难度远低于夹批。样张：p0162（第 8 回末）。\n")
    lines.append("9. **书格黑白版可绕网盘直下**：bw.shuge.org 是 OpenList（AList 分支），"
                 "对分享码 `POST /api/fs/get {\"path\":\"/@s/<code>\"}` 得 raw_url，直链支持 Range 206，"
                 "可分块并发断点续传（`download_shuge_pdf.py`）。已借此直下世德堂本 PDF 1.53 GB/1298 页/约 300 dpi。\n")

    lines.append("\n## 参数说明\n")
    lines.append("- `--size 2400,`：IIIF 宽度 2400px（约 360 dpi）。实测原图 5243px 与 3600px 均会中途断流，2400px 是稳定上限。\n")
    lines.append("- `--workers 6`：并发线程数。\n")
    lines.append("- 单册 265–364 页，实测约 2 页/分钟，全量 10 册共 2973 页需约 24 小时，可分多次中断续跑。\n")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("已写入 %s" % OUT)
    print("图像 %d 张 / %.1f MB" % (total_jpg, total_mb))
    for r in rows:
        if r["total"]:
            print("  %-24s %4d / %-4d %s" % (r["dir"], r["got"], r["total"],
                                             "完成" if r["got"] >= r["total"] else ""))
        else:
            print("  %-24s %4d / ?" % (r["dir"], r["got"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
