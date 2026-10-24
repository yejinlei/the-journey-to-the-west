# -*- coding: utf-8 -*-
"""抓取维基文库《西游记》100 回正文。

产物：
  06_文本源/wiki/raw/wiki_ch{001-100}.txt     每回 wiki markup 原文
  06_文本源/wiki/titles.json                  抓取到的子页清单
  docs/data/editions.parquet                  增加 wiki 版本记录

回失败不中断，重试 5 次，全部失败记 log 后跳过。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "06_文本源" / "wiki" / "raw"
TXT = ROOT / "06_文本源" / "wiki" / "txt"
RAW.mkdir(parents=True, exist_ok=True)
TXT.mkdir(parents=True, exist_ok=True)

API = "https://zh.wikisource.org/w/api.php"
UA = "Journey-to-the-WestKG/0.3 (research; contact: dev@t480.local)"

CJK = re.compile(r"[\u4e00-\u9fff]")
# 简单 wiki markup → 纯文本
TMPL = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<nowiki>.*?</nowiki>", re.S)
H1 = re.compile(r"^=\s*(.+?)\s*=+\s*$", re.M)
H2 = re.compile(r"^==\s*(.+?)\s*==\s*$", re.M)
H3 = re.compile(r"^===\s*(.+?)\s*===\s*$", re.M)
LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
URL = re.compile(r"\[https?://[^\]]+\]")
EXTLINK = re.compile(r"\[https?://[^\s\]]+\s+([^\]]+)\]")
BOLD = re.compile(r"''(.+?)''")
IT = re.compile(r"\'\'(.+?)\'\'")
REF_INLINE = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", re.S)


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
    raise RuntimeError(f"fail after {retries} tries: {url[:100]}... ({last})")


def strip_wiki_markup(text: str) -> str:
    t = TMPL.sub("", text)
    t = REF_INLINE.sub("", t)
    t = EXTLINK.sub(r"\1", t)
    t = URL.sub("", t)
    t = LINK.sub(lambda m: m.group(2) or m.group(1), t)
    t = BOLD.sub(r"\1", t)
    t = IT.sub(r"\1", t)
    t = H3.sub("\n### \1\n", t)
    t = H2.sub("\n## \1\n", t)
    t = H1.sub("\n# \1\n", t)
    t = re.sub(r"\{\{.*?\}\}", "", t, flags=re.S)  # template
    t = re.sub(r"#\w+\s*:", "", t)  # wikilink prefixes
    t = re.sub(r"^\s*[-*]\s*", "", t, flags=re.M)  # list bullet
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def split_lines(text: str) -> list[str]:
    """按自然行切：句读标点断行"""
    # 先把标题/分隔行拆出来
    parts = re.split(r"\n+", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p.startswith("#"):
            out.append(p)
            continue
        # 中文按 ~30 字切
        if len(p) > 60 and CJK.search(p):
            cur = ""
            for ch in p:
                cur += ch
                if len(cur) >= 28 and ch in "，。！？；、：）":
                    out.append(cur.strip())
                    cur = ""
            if cur.strip():
                out.append(cur.strip())
        else:
            out.append(p)
    return out


def main() -> int:
    print("[1/3] 查询维基子页 ...")
    try:
        d = api_get({
            "action": "query", "list": "allpages",
            "apprefix": "西游记/第", "aplimit": 500, "format": "json", "formatversion": 2,
        })
    except Exception as e:
        print(f"  子页列表失败：{e}", file=sys.stderr)
        print("  fallback: 直接按 1..100 尝试")
        titles = [f"西游记/第{i:03d}回" for i in range(1, 101)]
    else:
        titles = [p["title"] for p in d["query"]["allpages"]]
    print(f"  共 {len(titles)} 个子页；前 3: {titles[:3]}")

    print("[2/3] 抓正文 ...")
    results = []
    for i, title in enumerate(titles, 1):
        target = RAW / f"wiki_ch{i:03d}.txt"
        if target.exists() and target.stat().st_size > 200:
            print(f"  {i:>3}/{len(titles)}  跳过 (已有) {title}")
            results.append({"index": i, "title": title, "bytes": target.stat().st_size, "lines": -1})
            continue
        try:
            d = api_get({
                "action": "query", "prop": "revisions",
                "titles": title, "rvprop": "content", "format": "json", "formatversion": 2,
            })
            p = d["query"]["pages"][0]
            content = p.get("revisions", [{}])[0].get("content", "")
        except Exception as e:
            print(f"  {i:>3}/{len(titles)}  失败 {title}: {e}")
            results.append({"index": i, "title": title, "error": str(e)})
            continue
        if not content:
            print(f"  {i:>3}/{len(titles)}  空 {title}")
            results.append({"index": i, "title": title, "error": "empty content"})
            continue
        target.write_text(content, encoding="utf-8")
        clean = strip_wiki_markup(content)
        (TXT / f"wiki_ch{i:03d}.txt").write_text(clean, encoding="utf-8")
        lines = split_lines(clean)
        print(f"  {i:>3}/{len(titles)}  ok  {title}  {len(clean)}字  {len(lines)}行")
        results.append({"index": i, "title": title, "bytes": len(clean), "lines": len(lines)})
        time.sleep(0.6)

    (ROOT / "06_文本源" / "wiki" / "titles.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 更新 editions 表
    ok = sum(1 for r in results if r.get("lines", 0) > 0)
    err = sum(1 for r in results if "error" in r)
    print(f"[3/3] 抓完：成功 {ok} 回，失败 {err} 回")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
