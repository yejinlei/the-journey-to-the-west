# -*- coding: utf-8 -*-
"""批量抓取维基文库更多西游记版本（v0.9）。

版本清单：
  xiyouji_zhuan   —— 西游記傳/卷1-4           （杨致和简本，4卷41则）
  xiyou_yuanzhi   —— 西游原旨                  （刘一明评点节选，单页）
  xiyou_bu        —— 西遊補/序+第1-16回        （董说补书，17页）
  hou_xiyouji     —— 後西遊記/序+第1-40回      （后西游记，41页）
  xu_xiyouji      —— 續西遊記/序+第001-100回   （续西游记，101页）
  yangdonglai_ping —— 楊東來先生批評西游記/*    （PDF占位，仅存档）

产物：
  06_文本源/wiki/raw/{edition}_p{idx}.txt     维基 markup 原文
  06_文本源/wiki/txt/{edition}_p{idx}.txt     清洗后的纯文本（PDF占位版无 txt）
  06_文本源/wiki/titles_{edition}.json         抓取清单（含 title/idx/pdf_only/chars）

用法：
  python fetch_more_editions.py                 # 全部抓
  python fetch_more_editions.py xiyou_bu        # 只抓指定版
  python fetch_more_editions.py --sample 3      # 每版抽 3 页试抓
"""
import json
import re
import sys
import time
from pathlib import Path

# 复用 fetch_all_editions 的基础设施
from fetch_all_editions import api_get, strip_wiki_markup, API, UA

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "06_文本源" / "wiki" / "raw"
TXT = ROOT / "06_文本源" / "wiki" / "txt"
RAW.mkdir(parents=True, exist_ok=True)
TXT.mkdir(parents=True, exist_ok=True)

PDF_RE = re.compile(r"<pages\s+index=")

# ---------- 版本配置 ----------
EDITIONS_MORE = {
    "xiyouji_zhuan": {
        "display": "杨致和《西游记传》（简本，4卷41则）",
        "mode": "apprefix",
        "apprefix": "西遊記傳/",
        # 过滤：只保留正文卷页（卷1-4），排除主目录页
        "filter": lambda t: "/卷" in t and not t.endswith("西遊記傳"),
        "sort_key": lambda t: t,  # 按标题排序
    },
    "xiyou_yuanzhi": {
        "display": "刘一明《西游原旨》（丹道评点，100回诗诀）",
        "mode": "titles",
        "titles": ["西遊原旨"],
    },
    "xiyou_bu": {
        "display": "董说《西游补》16回",
        "mode": "apprefix",
        "apprefix": "西遊補/",
        "filter": None,
        "sort_key": lambda t: t,
    },
    "hou_xiyouji": {
        "display": "《后西游记》40回",
        "mode": "apprefix",
        "apprefix": "後西遊記/",
        "filter": None,
        "sort_key": lambda t: t,
    },
    "xu_xiyouji": {
        "display": "《续西游记》100回",
        "mode": "apprefix",
        "apprefix": "續西遊記/",
        "filter": None,
        "sort_key": lambda t: t,
    },
    "yangdonglai_ping": {
        "display": "杨东来批评西游记（PDF占位）",
        "mode": "apprefix",
        "apprefix": "楊東來先生批評西游記/",
        "filter": None,
        "sort_key": lambda t: t,
        "pdf_expected": True,
    },
}


def list_subpages(prefix: str) -> list[str]:
    """用 allpages 自动发现子页面。"""
    pages = []
    apcontinue = None
    while True:
        params = {
            "action": "query", "list": "allpages",
            "apprefix": prefix, "aplimit": 500,
            "format": "json", "formatversion": 2,
        }
        if apcontinue:
            params["apcontinue"] = apcontinue
        d = api_get(params)
        for p in d["query"]["allpages"]:
            pages.append(p["title"])
        apcontinue = d.get("continue", {}).get("apcontinue")
        if not apcontinue:
            break
    return sorted(pages)


def fetch_one(eid: str, idx: int, title: str) -> dict:
    """抓单页 → raw/txt 落盘。含 <pages index= 时只存 raw，标 pdf_only。"""
    raw_target = RAW / f"{eid}_p{idx:03d}.txt"
    txt_target = TXT / f"{eid}_p{idx:03d}.txt"

    # 增量：已存在且非空则跳过
    if raw_target.exists() and raw_target.stat().st_size > 200:
        # 检查是否 PDF 占位
        raw_content = raw_target.read_text(encoding="utf-8")
        is_pdf = bool(PDF_RE.search(raw_content))
        return {"idx": idx, "title": title, "skip": True,
                "bytes": raw_target.stat().st_size, "pdf_only": is_pdf}

    try:
        d = api_get({
            "action": "query", "prop": "revisions",
            "titles": title, "rvprop": "content", "rvslots": "main",
            "format": "json", "formatversion": 2,
        })
        p = d["query"]["pages"][0]
        content = p.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", "")
    except Exception as e:
        return {"idx": idx, "title": title, "error": str(e)}

    if not content:
        return {"idx": idx, "title": title, "error": "empty"}

    raw_target.write_text(content, encoding="utf-8")

    is_pdf = bool(PDF_RE.search(content))
    if is_pdf:
        # PDF 占位：只存 raw，不写 txt
        return {"idx": idx, "title": title, "bytes": len(content),
                "chars": len(content), "pdf_only": True}

    clean = strip_wiki_markup(content)
    txt_target.write_text(clean, encoding="utf-8")
    return {"idx": idx, "title": title, "bytes": len(clean), "chars": len(clean)}


def fetch_edition_more(eid: str, limit: int = 0, verbose: bool = True) -> list[dict]:
    cfg = EDITIONS_MORE[eid]

    # 构建标题列表
    if cfg["mode"] == "apprefix":
        titles = list_subpages(cfg["apprefix"])
        if cfg.get("filter"):
            titles = [t for t in titles if cfg["filter"](t)]
        if cfg.get("sort_key"):
            titles.sort(key=cfg["sort_key"])
    else:
        titles = cfg["titles"]

    if limit:
        titles = titles[:limit]
        print(f"  (limit={limit}, 只抓前 {len(titles)} 页)")

    results = []
    for i, title in enumerate(titles, 1):
        if verbose:
            print(f"  {i:>3}/{len(titles)}  fetch {title}", end="")
        r = fetch_one(eid, i, title)
        results.append(r)
        if verbose:
            if r.get("skip"):
                print("  skip")
            elif r.get("error"):
                print(f"  FAIL: {r['error']}")
            elif r.get("pdf_only"):
                print(f"  PDF  {r['bytes']}字")
            else:
                print(f"  ok   {r['chars']}字")
        time.sleep(0.5)
    return results


def main() -> int:
    if not sys.stdout.encoding or sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    args = sys.argv[1:]
    sample = 0
    if "--sample" in args:
        i = args.index("--sample")
        sample = int(args[i + 1])
        args.pop(i + 1)
        args.pop(i)
    editions_to_fetch = args if args else list(EDITIONS_MORE.keys())

    grand_ok = grand_err = grand_pdf = 0
    for eid in editions_to_fetch:
        if eid not in EDITIONS_MORE:
            print(f"未知版本: {eid}")
            continue
        print(f"\n=== [{eid}] {EDITIONS_MORE[eid]['display']} ===")
        try:
            rs = fetch_edition_more(eid, limit=sample)
        except Exception as e:
            print(f"  {eid} 全失败: {e}")
            grand_err += 1
            continue
        ok = sum(1 for r in rs if r.get("bytes", 0) > 0 and "error" not in r and not r.get("pdf_only"))
        pdf = sum(1 for r in rs if r.get("pdf_only"))
        skip = sum(1 for r in rs if r.get("skip"))
        err = sum(1 for r in rs if "error" in r)
        grand_ok += ok
        grand_pdf += pdf
        grand_err += err
        (ROOT / "06_文本源" / "wiki" / f"titles_{eid}.json").write_text(
            json.dumps(rs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  {eid}: ok={ok} pdf={pdf} skip={skip} err={err}")

    print(f"\n=== 全部完成: 新增 {grand_ok} 页, PDF {grand_pdf} 页, 失败 {grand_err} 页 ===")
    return 0 if grand_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
