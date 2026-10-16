# -*- coding: utf-8 -*-
"""批量抓取维基文库西游记三版本：
  1. gubao            —— 西遊記/第001-100回           （古本，100 回）
  2. yangdonglai_ping —— 楊東來先生批評西游記/第1-6本 + 全本/圖/小引/目次/總論（杨东来评本，6 本 + 5 附件）
  3. baihui_xiangzhu  —— 西遊記百回詳注/1-100          （百回详注本，100 回）

产物：
  06_文本源/wiki/raw/{edition}_p{idx}.txt     维基 markup 原文
  06_文本源/wiki/txt/{edition}_p{idx}.txt     清洗后的纯文本
  06_文本源/wiki/titles_{edition}.json         抓取清单

用法：
  python fetch_all_editions.py                 # 全部抓
  python fetch_all_editions.py gubao           # 只抓指定版
  python fetch_all_editions.py --sample 3      # 每版抽 3 页试抓
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "06_文本源" / "wiki" / "raw"
TXT = ROOT / "06_文本源" / "wiki" / "txt"
RAW.mkdir(parents=True, exist_ok=True)
TXT.mkdir(parents=True, exist_ok=True)

API = "https://zh.wikisource.org/w/api.php"
UA = "JourneyKG/0.4 (research; contact: dev@t480.local)"

CJK = re.compile(r"[\u4e00-\u9fff]")
TMPL = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<nowiki>.*?</nowiki>", re.S)
H1 = re.compile(r"^=\s*(.+?)\s*=+\s*$", re.M)
H2 = re.compile(r"^==\s*(.+?)\s*==\s*$", re.M)
H3 = re.compile(r"^===\s*(.+?)\s*===\s*$", re.M)
LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
URL = re.compile(r"\[https?://[^\]]+\]")
EXTLINK = re.compile(r"\[https?://[^\s\]]+\s+([^\]]+)\]")
BOLD = re.compile(r"''(.+?)''")
REF_INLINE = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", re.S)


EDITIONS = {
    "gubao": {
        "display": "古本（维基《西遊記》，1592 世德堂系统）",
        "prefix": "西遊記/第",
        "suffix": "回",
        "count": 100,
        "pad": 3,
        "extra_titles": [],
    },
    "baihui_xiangzhu": {
        "display": "西遊記百回詳注（汇评类）",
        "prefix": "西遊記百回詳注/",
        "suffix": "",
        "count": 100,
        "pad": 1,
        "extra_titles": [],
    },
    # 杨东来评本：维基仅有 PDF 占位符（<pages index=...>），无正文文本，跳过
}


def api_get(params: dict, retries: int = 5, timeout: int = 30) -> dict:
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"{API}?{qs}"
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            print(f"  [retry {i+1}/{retries}] {e}", file=sys.stderr)
            time.sleep(2 + i * 4)
    raise RuntimeError(f"fail after {retries}: {url[:100]} ({last})")


def strip_wiki_markup(text: str) -> str:
    t = TMPL.sub("", text)
    t = REF_INLINE.sub("", t)
    t = EXTLINK.sub(r"\1", t)
    t = URL.sub("", t)
    t = LINK.sub(lambda m: m.group(2) or m.group(1), t)
    t = BOLD.sub(r"\1", t)
    t = H3.sub("\n### \1\n", t)
    t = H2.sub("\n## \1\n", t)
    t = H1.sub("\n# \1\n", t)
    t = re.sub(r"\{\{.*?\}\}", "", t, flags=re.S)
    t = re.sub(r"#\w+\s*:", "", t)
    t = re.sub(r"^\s*[-*]\s*", "", t, flags=re.M)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def fetch_edition(eid: str, limit: int = 0, verbose: bool = True) -> list[dict]:
    cfg = EDITIONS[eid]
    titles = []
    if cfg["pad"]:
        for i in range(1, cfg["count"] + 1):
            titles.append(f"{cfg['prefix']}{i:0{cfg['pad']}}{cfg['suffix']}")
    else:
        for i in range(1, cfg["count"] + 1):
            titles.append(f"{cfg['prefix']}{i}")
    for t in cfg["extra_titles"]:
        titles.append(f"{cfg['prefix'][:-1]}{t}" if cfg["prefix"].endswith("/") else f"{cfg['prefix']}/{t}")

    if limit:
        titles = titles[:limit]
        print(f"  (limit={limit}, 只抓前 {len(titles)} 页)")

    results = []
    for i, title in enumerate(titles, 1):
        raw_target = RAW / f"{eid}_p{i:03d}.txt"
        txt_target = TXT / f"{eid}_p{i:03d}.txt"
        if raw_target.exists() and raw_target.stat().st_size > 200:
            results.append({"idx": i, "title": title, "skip": True, "bytes": raw_target.stat().st_size})
            if verbose:
                print(f"  {i:>3}/{len(titles)}  skip {title}")
            continue
        try:
            d = api_get({
                "action": "query", "prop": "revisions",
                "titles": title, "rvprop": "content",
                "format": "json", "formatversion": 2,
            })
            p = d["query"]["pages"][0]
            content = p.get("revisions", [{}])[0].get("content", "")
        except Exception as e:
            print(f"  {i:>3}/{len(titles)}  FAIL {title}: {e}")
            results.append({"idx": i, "title": title, "error": str(e)})
            continue
        if not content:
            print(f"  {i:>3}/{len(titles)}  EMPTY {title}")
            results.append({"idx": i, "title": title, "error": "empty"})
            continue
        raw_target.write_text(content, encoding="utf-8")
        clean = strip_wiki_markup(content)
        txt_target.write_text(clean, encoding="utf-8")
        print(f"  {i:>3}/{len(titles)}  ok   {title}  {len(clean)}字")
        results.append({"idx": i, "title": title, "bytes": len(clean), "chars": len(clean)})
        time.sleep(0.5)
    return results


def main() -> int:
    if not sys.stdout.encoding or sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    # CLI
    args = sys.argv[1:]
    sample = 0
    if "--sample" in args:
        i = args.index("--sample")
        sample = int(args[i + 1])
        args.pop(i + 1); args.pop(i)
    editions_to_fetch = args if args else list(EDITIONS.keys())

    grand_ok = grand_err = 0
    for eid in editions_to_fetch:
        print(f"\n=== [{eid}] {EDITIONS[eid]['display']} ===")
        try:
            rs = fetch_edition(eid, limit=sample)
        except Exception as e:
            print(f"  {eid} 全失败: {e}")
            grand_err += 1
            continue
        ok = sum(1 for r in rs if r.get("bytes", 0) > 0 and "error" not in r)
        skip = sum(1 for r in rs if r.get("skip"))
        err = sum(1 for r in rs if "error" in r)
        grand_ok += ok
        grand_err += err
        (ROOT / "06_文本源" / "wiki" / f"titles_{eid}.json").write_text(
            json.dumps(rs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  {eid}: ok={ok} skip={skip} err={err}")

    print(f"\n=== 全部完成: 新增 {grand_ok} 页, 失败 {grand_err} 页 ===")
    return 0 if grand_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
