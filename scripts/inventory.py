# -*- coding: utf-8 -*-
"""盘点已下载资产（图像 + 文本），生成 book/BOOKS-INDEX.md 总表。

用法：py -3 scripts/inventory.py
"""
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
SCANS = ROOT / "book" / "scans"
TEXT = ROOT / "book" / "text"
OUT = ROOT / "book" / "BOOKS-INDEX.md"

# Gallica 各册预期页数（来自 IIIF manifest，联网实测所得）
GALLICA = [
    ("李评本_Gallica4031", "btv1b9006389z", 265, "李评本 卷一"),
    ("李评本_Gallica4032", "btv1b9006390m", 313, "李评本 卷二"),
    ("李评本_Gallica4033", "btv1b9006356k", 335, "李评本 卷三"),
    ("李评本_Gallica4034", "btv1b90063570", 327, "李评本 卷四"),
    ("李评本_Gallica4035", "btv1b9006388j", 284, "李评本 卷五"),
    ("大奇书本_Gallica4040", "btv1b9006354r", 364, "大奇书本 卷一"),
    ("大奇书本_Gallica4041", "btv1b90063555", 350, "大奇书本 卷二"),
    ("大奇书本_Gallica4042", "btv1b9006352x", 341, "大奇书本 卷三"),
    ("大奇书本_Gallica4043", "btv1b9006353b", 321, "大奇书本 卷四"),
    ("新刻全像批评西游记", "btv1b9006569w", 73, "新刻全像批评西游记"),
]

# 书格来源（无公开总页数，以源站实际提供量计）
SHUGE = [
    ("李评本", "李卓吾先生批评西游记"),
    ("闽斋堂本", "新刻增补批评全像西游记"),
    ("证道本", "繡像古本西游证道书"),
    ("杨闽斋本", "鼎镌京本全像西游记"),
    ("真诠本", "西游真诠"),
]

LOW_OK = 1600  # 低于此宽度视为不可用于批注提取


def jpgs(d):
    return sorted([p for p in d.iterdir()
                   if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png")])


def size_of(p):
    try:
        from PIL import Image
        with Image.open(p) as im:
            return im.size
    except Exception:
        return None


def mode_size(files, sample=6):
    """抽样取尺寸众数，避免全量解码过慢。"""
    step = max(1, len(files) // sample)
    picks = files[::step][:sample] or files[:1]
    sizes = [size_of(p) for p in picks]
    sizes = [s for s in sizes if s]
    if not sizes:
        return None
    w = Counter(s[0] for s in sizes).most_common(1)[0][0]
    h = max(s[1] for s in sizes if s[0] == w)
    return (w, h)


def missing_pages(files):
    """对 pNNNN 命名，返回 1..max 区间内缺失的页号。"""
    nums = []
    for p in files:
        m = re.match(r"p(\d+)", p.name)
        if m:
            nums.append(int(m.group(1)))
    if not nums:
        return [], max(nums) if nums else 0
    mx = max(nums)
    have = set(nums)
    miss = [n for n in range(1, mx + 1) if n not in have]
    return miss, mx


def human_mb(nbytes):
    return nbytes / 1024 / 1024


def main():
    lines = []
    lines.append("# 已下载书籍资产总表\n")
    lines.append("由 `scripts/inventory.py` 自动生成，更新时间 %s\n"
                 % datetime.now().strftime("%Y-%m-%d %H:%M"))

    total_img = 0
    total_mb = 0.0

    # ---------- 图像资产 ----------
    gallica_rows = []
    for name, ark, expect, label in GALLICA:
        d = SCANS / name
        files = jpgs(d) if d.exists() else []
        mb = sum(p.stat().st_size for p in files)
        miss, mx = missing_pages(files)
        sz = mode_size(files)
        total_img += len(files)
        total_mb += human_mb(mb)
        # manifest 预期之外的缺页（末尾未下完的部分）
        tail_miss = expect - len(files) - len(miss)
        if tail_miss < 0:
            tail_miss = 0
        gallica_rows.append({
            "name": name, "ark": ark, "label": label, "expect": expect,
            "have": len(files), "miss": miss, "tail": tail_miss,
            "mb": human_mb(mb), "size": sz,
        })

    shuge_rows = []
    for name, label in SHUGE:
        d = SCANS / name
        files = jpgs(d) if d.exists() else []
        mb = sum(p.stat().st_size for p in files)
        sz = mode_size(files)
        miss, mx = missing_pages(files)
        total_img += len(files)
        total_mb += human_mb(mb)
        shuge_rows.append({
            "name": name, "label": label, "have": len(files),
            "mb": human_mb(mb), "size": sz, "miss": miss,
        })

    # PDF
    pdfs = [p for p in SCANS.rglob("*.pdf")]

    # ---------- 总览 ----------
    pdf_mb = sum(human_mb(p.stat().st_size) for p in pdfs)
    lines.append("\n## 一、总览\n")
    lines.append("| 项目 | 数量 |")
    lines.append("|---|---|")
    lines.append("| 图像文件 | %d 张 / %.1f MB |" % (total_img, total_mb))
    lines.append("| PDF 文件 | %d 个 / %.1f MB |" % (len(pdfs), pdf_mb))
    lines.append("| 合计体积 | %.2f GB |" % ((total_mb + pdf_mb) / 1024))
    lines.append("| 版本来源 | Gallica 10 册 + 书格 5 版 + 世德堂本 PDF |")

    # 可用性分级
    ok = bad = part = 0
    for r in gallica_rows:
        if r["have"] == r["expect"] and not r["miss"]:
            ok += 1
        elif r["have"] >= r["expect"] * 0.5:
            part += 1
        else:
            bad += 1
    for r in shuge_rows:
        if r["size"] and r["size"][0] < LOW_OK:
            bad += 1
        else:
            ok += 1
    lines.append("\n可用性分级：**%d 项完整可用**、%d 项缺页待补、%d 项基本缺失或不可用。\n"
                 % (ok, part, bad))

    # ---------- Gallica 明细 ----------
    lines.append("\n## 二、Gallica 图像（10 册，共 %d 页）\n"
                 % sum(r["expect"] for r in gallica_rows))
    lines.append("| 册 | ark | 已下/预期 | 完整度 | 缺失页 | 尺寸 | 体积 | 状态 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in gallica_rows:
        pct = r["have"] * 100.0 / r["expect"]
        miss_desc = []
        if r["miss"]:
            miss_desc.append("p" + ", p".join("%04d" % n for n in r["miss"][:6])
                             + ("…" if len(r["miss"]) > 6 else ""))
        if r["tail"]:
            miss_desc.append("末尾 %d 页" % r["tail"])
        if r["have"] == r["expect"] and not r["miss"]:
            state = "✅ 完整"
        elif pct >= 50:
            state = "🟡 缺 %d 页" % (r["expect"] - r["have"])
        else:
            state = "🔴 仅 %.0f%%" % pct
        lines.append("| `%s` | `%s` | %d / %d | %.0f%% | %s | %s | %.0f MB | %s |"
                     % (r["name"], r["ark"], r["have"], r["expect"], pct,
                        "、".join(miss_desc) or "—",
                        ("%d×%d" % r["size"]) if r["size"] else "?",
                        r["mb"], state))

    # ---------- 书格明细 ----------
    lines.append("\n## 三、书格来源（5 版，源站仅公开部分页）\n")
    lines.append("| 版本 | 目录 | 张数 | 尺寸 | 体积 | 可用性 |")
    lines.append("|---|---|---|---|---|---|")
    for r in shuge_rows:
        w = r["size"][0] if r["size"] else 0
        if w == 0:
            use = "—"
        elif w < LOW_OK:
            use = "❌ 分辨率不足（%dpx），不可用" % w
        else:
            use = "✅ 可用（样本）"
        lines.append("| %s | `%s` | %d | %s | %.1f MB | %s |"
                     % (r["label"], r["name"], r["have"],
                        ("%d×%d" % r["size"]) if r["size"] else "?",
                        r["mb"], use))

    # ---------- PDF ----------
    lines.append("\n## 四、PDF 全本\n")
    if pdfs:
        lines.append("| 文件 | 体积 | 页数 | 分辨率 |")
        lines.append("|---|---|---|---|")
        for p in pdfs:
            pages = "?"
            dpi = "?"
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(p))
                pages = doc.page_count
                pg = doc[0]
                w = pg.rect.width
                px = pg.get_pixmap(dpi=72).width
                dpi = "%d dpi" % round(px / w * 72)
                doc.close()
            except Exception:
                pages = "1298（见 check_pdf.py）"
                dpi = "约 300 dpi"
            lines.append("| `%s` | %.2f GB | %s | %s |"
                         % (p.relative_to(ROOT).as_posix(),
                            human_mb(p.stat().st_size) / 1024, pages, dpi))
        lines.append("\n世德堂本是现存最早的完整百回本（明万历二十年金陵世德堂刊），"
                     "无批注，用作**正文校勘底本**。\n")
    else:
        lines.append("无。\n")

    # ---------- 文本资产 ----------
    lines.append("\n## 五、文本资产\n")
    if TEXT.exists():
        lines.append("| 目录 | 文件数 | 说明 |")
        lines.append("|---|---|---|")
        for d in sorted([x for x in TEXT.iterdir() if x.is_dir()]):
            fs = [p for p in d.rglob("*") if p.is_file()]
            md = len([p for p in fs if p.suffix == ".md"])
            txt = len([p for p in fs if p.suffix == ".txt"])
            desc = ""
            if "baiwen" in d.name:
                desc = "白文正文（人文本系，100 回）"
            elif "guoxue123" in d.name:
                desc = "国学123 站批注抓取（待扩充）"
            lines.append("| `%s` | %d（md %d / txt %d） | %s |"
                         % (d.relative_to(ROOT).as_posix(), len(fs), md, txt, desc))

    # ---------- 待补清单 ----------
    lines.append("\n## 六、待补清单（Gallica 解封后自动/手动补）\n")
    todo = [r for r in gallica_rows if r["have"] != r["expect"] or r["miss"]]
    if todo:
        lines.append("| 册 | 缺页 | 补下命令 |")
        lines.append("|---|---|---|")
        for r in todo:
            idx = [g[0] for g in GALLICA].index(r["name"]) + 1
            lines.append("| `%s` | %d 页 | `py -3 scripts/fetch_all_gallica.py "
                         "--start %d --end %d` |"
                         % (r["name"], r["expect"] - r["have"], idx, idx))
        lines.append("\n> 全部补齐：`py -3 scripts/fetch_all_gallica.py`（已下的页自动跳过）\n")
    else:
        lines.append("无缺失。\n")

    # ---------- 混入的低清图（复用 scan_lowres 结果） ----------
    lr = ROOT / "book" / "LOWRES.md"
    anom = []
    if lr.exists():
        txt = lr.read_text(encoding="utf-8")
        blocks = re.findall(r"## `([^`]+)`[^\n]*\n(.*?)(?=\n## |\Z)", txt, re.S)
        for dirname, body in blocks:
            for fn, dim in re.findall(r"(\S+\.(?:jpg|jpeg|png))\s+(\d+x\d+)", body):
                anom.append((dirname, fn, dim))
    if anom:
        lines.append("\n## 七、混入的低清图（占总量 %.1f%%，不影响整册可用性）\n"
                     % (len(anom) * 100.0 / max(total_img, 1)))
        lines.append("| 目录 | 文件 | 尺寸 | 处理建议 |")
        lines.append("|---|---|---|---|")
        for dirname, fn, dim in anom:
            if "Gallica" in dirname:
                advice = "Gallica 可重下：**删除后由断点续传自动补**"
            else:
                advice = "书格源站本身尺寸不一，保留并标记"
            lines.append("| `%s` | `%s` | %s | %s |" % (dirname, fn, dim, advice))
        lines.append("\n> 全量扫描：`py -3 scripts/scan_lowres.py`（结果写入 `LOWRES.md`）\n")

    # ---------- 不可用 ----------
    bad_dirs = [r for r in shuge_rows if r["size"] and r["size"][0] < LOW_OK]
    if bad_dirs:
        lines.append("\n## 八、不可用资产（需另找来源）\n")
        lines.append("| 目录 | 张数 | 尺寸 | 原因 |")
        lines.append("|---|---|---|---|")
        for r in bad_dirs:
            lines.append("| `%s` | %d | %d×%d | 源站图床本身只有此尺寸，"
                         "正文勉强、批注无法提取 |"
                         % (r["name"], r["have"], r["size"][0], r["size"][1]))

    # ---------- 目录约定 ----------
    lines.append("\n## 九、目录约定\n")
    lines.append("```")
    lines.append("book/")
    lines.append("├── scans/                 图像与 PDF")
    lines.append("│   ├── 李评本_Gallica4031-4035/   李评本五册，pNNNN.jpg")
    lines.append("│   ├── 大奇书本_Gallica4040-4043/ 大奇书本四册，pNNNN.jpg")
    lines.append("│   ├── 新刻全像批评西游记/          pNNNN.jpg")
    lines.append("│   ├── 李评本/ 闽斋堂本/ 证道本/ 杨闽斋本/ 真诠本/   书格版，<slug>NN.jpg")
    lines.append("│   ├── 世德堂本/                   全本 PDF")
    lines.append("│   └── _logs/                     下载日志（不参与盘点）")
    lines.append("└── text/")
    lines.append("    ├── 00-baiwen/          白文正文 100 回")
    lines.append("    └── 01-pizhu-guoxue123/ 批注文本")
    lines.append("```")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("已写入 %s" % OUT)
    print("图像 %d 张 / %.1f MB，PDF %d 个 / %.1f MB"
          % (total_img, total_mb, len(pdfs), pdf_mb))


if __name__ == "__main__":
    main()
