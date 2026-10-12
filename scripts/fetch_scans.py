#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古籍扫描下载脚本（面向《西游记》各评点本）

用途：从 Internet Archive / 哈佛数字馆藏 检索并下载古籍扫描图像，
      输出到 book/scans/<版本>/，并测量分辨率以判断批注可否提取。

用法示例：
  # 1) 按预设检索全部评点本，列出候选
  py -3 scripts/fetch_scans.py search --all-presets
  py -3 scripts/fetch_scans.py search --preset lizhuowu
  py -3 scripts/fetch_scans.py search --query "西游证道书"

  # 2) 下载指定资源（优先高清逐页图像）
  py -3 scripts/fetch_scans.py fetch --id <identifier> --edition 李评本

  # 3) 测量已下载图像的分辨率
  py -3 scripts/fetch_scans.py verify --dir book/scans/李评本

代理：
  --proxy http://127.0.0.1:7890

注意：中华古籍资源库（read.nlc.cn）需登录且无公开批量接口，
      本脚本不对其进行自动下载，仅给出检索入口（见 --source nlc）。
"""

import argparse
import json
import os
import struct
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

# 汇评本涉及的各版本检索预设：slug -> (中文目录名, [检索词...])
PRESETS = {
    "shidetang": ("世德堂本", ["新刻官板大字西游记", "世德堂 西游记", "Journey to the West Wanli"]),
    "lizhuowu": ("李评本", ["李卓吾先生批评西游记", "李卓吾 批评 西游记", "Li Zhuowu xiyouji"]),
    "zhengdao": ("证道本", ["西游证道书", "西游証道書", "西游证道奇书"]),
    "zhenquan": ("真诠本", ["西游真诠", "西遊真詮"]),
    "xinshuo": ("新说本", ["新说西游记", "新說西遊記", "新说西游记图像"]),
    "yuanzhi": ("原旨本", ["西游原旨", "西遊原旨"]),
    "zhengzhi": ("正旨本", ["通易西游正旨", "通易西遊正旨"]),
    "hanping": ("含评本", ["西游记评注", "西遊記評注", "含晶子"]),
    "qingchao": ("清抄本", ["西游记记", "西遊記記"]),
}

# 下载格式优先级：越靠前越适合提取批注
FORMAT_PRIORITY = [
    ("jp2", "_jp2.zip"),          # JPEG2000 逐页，最高清
    ("raw_jp2", "_raw_jp2.zip"),
    ("tif", "_tif.zip"),
    ("images", "_images.zip"),
    ("pdf", ".pdf"),
]


def make_opener(proxy=None):
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener(*handlers)


def http_get(url, proxy=None, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with make_opener(proxy).open(req, timeout=timeout) as r:
        return r.read()


def http_json(url, proxy=None, timeout=60):
    return json.loads(http_get(url, proxy, timeout).decode("utf-8", "replace"))


# ---------- 检索 ----------

def search_archive(query, proxy=None, rows=20):
    q = urllib.parse.urlencode({
        "q": query,
        "fl[]": ["identifier", "title", "year", "mediatype", "collection"],
        "rows": rows,
        "page": 1,
        "output": "json",
    }, doseq=True)
    url = "https://archive.org/advancedsearch.php?" + q
    try:
        data = http_json(url, proxy, timeout=40)
    except Exception as e:
        return None, f"检索失败: {e}"
    docs = data.get("response", {}).get("docs", [])
    return docs, None


def search_harvard(query, proxy=None, rows=20):
    url = "https://collections.library.harvard.edu/catalog.json?" + urllib.parse.urlencode(
        {"q": query, "rows": rows})
    try:
        data = http_json(url, proxy, timeout=40)
    except Exception as e:
        return None, f"检索失败: {e}"
    out = []
    for d in data.get("data", [])[:rows]:
        attrs = d.get("attributes", {})
        out.append({
            "identifier": str(attrs.get("id", "")),
            "title": str(attrs.get("title", {}).get("primary", [""])[0]),
            "year": "",
        })
    return out, None


def cmd_search(args):
    proxy = args.proxy
    targets = []
    if args.all_presets:
        targets = list(PRESETS.items())
    elif args.preset:
        if args.preset not in PRESETS:
            print(f"未知预设: {args.preset}；可用: {', '.join(PRESETS)}")
            return 1
        targets = [(args.preset, PRESETS[args.preset])]
    elif args.query:
        targets = [("custom", (args.query, [args.query]))]
    else:
        print("需指定 --all-presets / --preset / --query 之一")
        return 1

    for slug, (name, queries) in targets:
        print(f"\n=== {name} [{slug}] ===")
        for q in queries:
            if args.source == "archive":
                docs, err = search_archive(q, proxy, args.rows)
            else:
                docs, err = search_harvard(q, proxy, args.rows)
            if err:
                print(f"  [{q}] {err}")
                continue
            print(f"  [{q}] 命中 {len(docs)}")
            for d in docs[:args.rows]:
                t = d.get("title", "")
                if isinstance(t, list):
                    t = t[0] if t else ""
                print(f"    {d.get('identifier','')} | {t} | {d.get('year','')}")
            time.sleep(0.6)
    return 0


# ---------- 下载 ----------

def pick_best_file(files, prefer):
    """按格式优先级挑选最佳下载文件。"""
    if prefer:
        for f in files:
            if f["name"].lower().endswith(prefer.lower()):
                return f
    for _label, suffix in FORMAT_PRIORITY:
        for f in files:
            if f["name"].lower().endswith(suffix):
                return f
    # 退而求其次：最大的文件
    if files:
        return max(files, key=lambda f: int(f.get("size", 0) or 0))
    return None


def download(url, dest, proxy=None):
    opener = make_opener(proxy)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    dest.parent.mkdir(parents=True, exist_ok=True)
    with opener.open(req, timeout=120) as r, open(dest, "wb") as out:
        total = int(r.headers.get("Content-Length", 0) or 0)
        done = 0
        t0 = time.time()
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                pct = done * 100 // total
                print(f"\r    下载 {done}/{total} 字节 ({pct}%)", end="", flush=True)
        print()
    return done, time.time() - t0


def cmd_fetch(args):
    proxy = args.proxy
    out_dir = Path(args.out) / args.edition
    raw_dir = out_dir / "raw"
    pages_dir = out_dir / "pages"

    print(f"读取资源元数据: {args.id}")
    try:
        meta = http_json(f"https://archive.org/metadata/{args.id}", proxy, timeout=60)
    except Exception as e:
        print(f"元数据获取失败: {e}")
        return 1

    server = meta.get("server", "archive.org")
    dpath = meta.get("dir", "")
    files = [f for f in meta.get("files", []) if f.get("name")]
    if not files:
        print("该资源没有可下载文件")
        return 1

    chosen = pick_best_file(files, args.prefer)
    if not chosen:
        print("未找到合适文件")
        return 1

    fname = chosen["name"]
    url = f"https://{server}/{dpath}/{urllib.parse.quote(fname)}"
    print(f"选定文件: {fname}  ({int(chosen.get('size',0) or 0)} 字节)")

    if args.dry_run:
        print(f"[dry-run] 将下载 {url}\n          -> {raw_dir / fname}")
        return 0

    dest = raw_dir / fname
    n, secs = download(url, dest, proxy)
    print(f"完成: {n} 字节, 用时 {secs:.1f}s -> {dest}")

    extracted = []
    if fname.lower().endswith(".zip"):
        try:
            pages_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dest) as z:
                z.extractall(pages_dir)
            extracted = sorted(p.name for p in pages_dir.rglob("*") if p.is_file())
            print(f"已解压 {len(extracted)} 个文件 -> {pages_dir}")
        except Exception as e:
            print(f"解压失败: {e}")

    manifest = {
        "edition": args.edition,
        "identifier": args.id,
        "source": "archive.org",
        "file": fname,
        "url": url,
        "bytes": n,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "extracted_count": len(extracted),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out_dir / 'manifest.json'}")

    if extracted or not fname.lower().endswith(".zip"):
        return cmd_verify(argparse.Namespace(dir=str(pages_dir if extracted else raw_dir), page_cm=args.page_cm))
    return 0


# ---------- 分辨率测量 ----------

def jpeg_size(path):
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seg
    return None


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def jp2_size(path):
    with open(path, "rb") as f:
        data = f.read(4096)
    p = data.find(b"ihdr")
    if p < 0:
        return None
    h, w = struct.unpack(">II", data[p + 4:p + 12])
    return w, h


def image_size(path):
    ext = path.suffix.lower()
    try:
        if ext in (".jpg", ".jpeg"):
            return jpeg_size(path)
        if ext == ".png":
            return png_size(path)
        if ext in (".jp2", ".jpf", ".jpx"):
            return jp2_size(path)
    except Exception:
        return None
    return None


def dpi_verdict(dpi):
    if dpi >= 600:
        return "夹批可用（推荐）"
    if dpi >= 400:
        return "眉批可用，夹批勉强"
    if dpi >= 300:
        return "仅回评/大字可靠，夹批基本不可用"
    return "分辨率过低，批注无法提取"


def cmd_verify(args):
    d = Path(args.dir)
    if not d.exists():
        print(f"目录不存在: {d}")
        return 1
    imgs = [p for p in sorted(d.rglob("*")) if p.is_file()
            and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".jp2", ".jpf", ".jpx")]
    if not imgs:
        print(f"未找到图像文件: {d}")
        print("（若是 PDF，请先自行转换为图像，或检查该 PDF 是否含文本层）")
        return 1

    print(f"\n图像总数: {len(imgs)}")
    sample = imgs[:3] + imgs[len(imgs) // 2:len(imgs) // 2 + 1]
    print(f"页面物理宽度按 {args.page_cm} cm 估算：\n")
    print(f"{'文件':<32}{'宽x高(px)':<20}{'估算DPI':<10}判定")
    print("-" * 90)
    for p in sample:
        sz = image_size(p)
        if not sz:
            print(f"{p.name:<32}{'(无法测量)':<20}")
            continue
        w, h = sz
        dpi = w / (args.page_cm / 2.54)
        print(f"{p.name:<32}{f'{w}x{h}':<20}{dpi:<10.0f}{dpi_verdict(dpi)}")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="古籍扫描下载与分辨率核查")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="检索候选资源")
    s.add_argument("--preset", choices=list(PRESETS))
    s.add_argument("--all-presets", action="store_true")
    s.add_argument("--query")
    s.add_argument("--source", choices=["archive", "harvard"], default="archive")
    s.add_argument("--rows", type=int, default=10)
    s.add_argument("--proxy")
    s.set_defaults(func=cmd_search)

    f = sub.add_parser("fetch", help="下载资源")
    f.add_argument("--id", required=True, help="archive.org identifier")
    f.add_argument("--edition", required=True, help="版本中文名，作为输出子目录")
    f.add_argument("--out", default="book/scans")
    f.add_argument("--prefer", help="指定文件名后缀，如 _jp2.zip")
    f.add_argument("--page-cm", type=float, default=17.0, help="页面物理宽度(cm)，用于估算 DPI")
    f.add_argument("--proxy")
    f.add_argument("--dry-run", action="store_true")
    f.set_defaults(func=cmd_fetch)

    v = sub.add_parser("verify", help="测量已下载图像分辨率")
    v.add_argument("--dir", required=True)
    v.add_argument("--page-cm", type=float, default=17.0)
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
