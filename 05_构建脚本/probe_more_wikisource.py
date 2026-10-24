# -*- coding: utf-8 -*-
"""探针：确认维基文库上各候选版本的子页面结构、标题用字、内容类型。

只读+打印，不写文件。

用法：
  python probe_more_wikisource.py            # 全部探
  python probe_more_wikisource.py xiyou_bu   # 只探指定版
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://zh.wikisource.org/w/api.php"
UA = "JourneyKG/0.9 (research; contact: dev@t480.local)"

# 候选版本配置
CANDIDATES = {
    "xiyouji_zhuan": {
        "desc": "杨致和《西游记传》（简本，4卷41则）",
        "apprefix": "西游記傳/",
    },
    "xiyou_yuanzhi": {
        "desc": "刘一明《西游原旨》（评点节选）",
        "titles": ["西游原旨"],
    },
    "xiyou_bu": {
        "desc": "董说《西游补》16回",
        "apprefix": "西遊補/",
    },
    "hou_xiyouji": {
        "desc": "《后西游记》40回",
        "apprefix": "後西遊記/",
    },
    "xu_xiyouji": {
        "desc": "《续西游记》100回",
        "apprefix": "續西遊記/",
    },
    "yangdonglai_ping": {
        "desc": "杨东来批评西游记（PDF占位）",
        "apprefix": "楊東來先生批評西游記/",
    },
}


def api_get(params: dict, retries: int = 3, timeout: int = 30) -> dict:
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
            time.sleep(1 + i * 2)
    raise RuntimeError(f"fail after {retries}: {url[:100]} ({last})")


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


def probe_page(title: str) -> dict:
    """探测单页内容类型和结构。"""
    d = api_get({
        "action": "query", "titles": title,
        "prop": "revisions", "rvprop": "content", "rvslots": "main",
        "format": "json", "formatversion": 2,
    })
    pg = d["query"]["pages"][0]
    if "missing" in pg:
        return {"title": title, "missing": True}
    content = pg.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", "")
    has_pages_tag = bool(re.search(r"<pages\s+index=", content))
    has_transclusion = bool(re.search(r"\{\{[:：]", content))
    # 找标题结构
    h2 = re.findall(r"^==\s*(.+?)\s*==\s*$", content, re.M)
    h3 = re.findall(r"^===\s*(.+?)\s*===\s*$", content, re.M)
    # 找回目标记
    ch_marks = re.findall(r"第[一二三四五六七八九十百零〇0-9]+回", content)
    return {
        "title": title,
        "chars": len(content),
        "has_pages_tag": has_pages_tag,
        "has_transclusion": has_transclusion,
        "h2_count": len(h2),
        "h2_sample": h2[:5],
        "h3_count": len(h3),
        "h3_sample": h3[:5],
        "chapter_marks": len(ch_marks),
        "chapter_sample": ch_marks[:5],
        "head_300": content[:300],
    }


def probe_candidate(eid: str, cfg: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  [{eid}] {cfg['desc']}")
    print(f"{'='*60}")

    if "apprefix" in cfg:
        prefix = cfg["apprefix"]
        print(f"  模式: apprefix={prefix}")
        pages = list_subpages(prefix)
        print(f"  子页面数: {len(pages)}")
        for p in pages[:3]:
            print(f"    {p}")
        if len(pages) > 3:
            print(f"    ... 共 {len(pages)} 个")
        # 探前3个子页
        for p in pages[:3]:
            info = probe_page(p)
            if info.get("missing"):
                print(f"    MISS {p}")
            else:
                pdf = "PDF" if info["has_pages_tag"] else "TEXT"
                trans = "TRANS" if info["has_transclusion"] else ""
                print(f"    {info['title']}  {info['chars']}字  {pdf} {trans}")
                if info["h2_sample"]:
                    print(f"      H2: {info['h2_sample']}")
                if info["chapter_sample"]:
                    print(f"      回目: {info['chapter_sample']}")
                print(f"      前200字: {info['head_300'][:200]}")
            time.sleep(0.3)

    elif "titles" in cfg:
        print(f"  模式: 显式标题列表")
        for t in cfg["titles"]:
            info = probe_page(t)
            if info.get("missing"):
                print(f"    MISS {t}")
            else:
                pdf = "PDF" if info["has_pages_tag"] else "TEXT"
                trans = "TRANS" if info["has_transclusion"] else ""
                print(f"    {info['title']}  {info['chars']}字  {pdf} {trans}")
                if info["h2_sample"]:
                    print(f"      H2: {info['h2_sample']}")
                if info["chapter_sample"]:
                    print(f"      回目: {info['chapter_sample']}")
                print(f"      前200字: {info['head_300'][:200]}")
            time.sleep(0.3)


def main() -> int:
    if not sys.stdout.encoding or sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    args = sys.argv[1:]
    targets = args if args else list(CANDIDATES.keys())

    for eid in targets:
        if eid not in CANDIDATES:
            print(f"未知版本: {eid}")
            continue
        try:
            probe_candidate(eid, CANDIDATES[eid])
        except Exception as e:
            print(f"  [{eid}] 探测失败: {e}")

    print(f"\n{'='*60}")
    print("  探针完成")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
