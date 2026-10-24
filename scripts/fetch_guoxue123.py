#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取国学导航「汇评证道西游记」等批注文本页，输出纯文本。

用法：
  py -3 scripts/fetch_guoxue123.py --list           # 列出目录页中的所有页面
  py -3 scripts/fetch_guoxue123.py --download       # 下载全部页面为 txt
"""
import argparse
import re
import sys
import time
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

BASE = "http://www.guoxue123.com/xiaosuo/jd/hpxyj/"
INDEX_CANDIDATES = ["index.htm", "000.htm", "001.htm"]
OUT = Path("book/text/01-pizhu-guoxue123")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=30).read()
    for enc in ("utf-8", "gb18030", "gbk"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def page_links(html):
    """提取同目录下的页面编号链接。"""
    nums = set()
    for m in re.finditer(r'href="([^"]*?/?)(\d{3})\.htm"', html):
        nums.add(m.group(2))
    return sorted(nums)


def clean(html):
    s = re.sub(r"(?s)<script.*?</script>", "", html)
    s = re.sub(r"(?s)<style.*?</style>", "", s)
    s = re.sub(r"(?s)<!--.*?-->", "", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</p>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--max", type=int, default=200)
    args = ap.parse_args()

    html = get(BASE + "001.htm")
    nums = set(page_links(html))
    print("从 001.htm 发现页码: %s" % (sorted(nums)[:20]))

    # 目录页 000.htm 通常列出全部章节
    try:
        idx = get(BASE + "000.htm")
        n2 = set(page_links(idx))
        print("从 000.htm 发现页码: %d 个 -> %s" % (len(n2), sorted(n2)[:20]))
        nums |= n2
    except Exception as e:
        print("000.htm 获取失败: %s" % str(e)[:60])
    nums = sorted(nums)

    # 若未发现，尝试按序号探测
    if not nums:
        nums = ["%03d" % i for i in range(1, args.max + 1)]
        print("改用顺序探测 001-%03d" % args.max)

    if args.list:
        for n in nums[:50]:
            print("   " + BASE + n + ".htm")
        return 0

    if not args.download:
        print("需指定 --list 或 --download")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    ok, fail = 0, 0
    for n in nums:
        url = BASE + n + ".htm"
        dest = OUT / ("%s.txt" % n)
        if dest.exists() and dest.stat().st_size > 0:
            ok += 1
            continue
        try:
            h = get(url)
            txt = clean(h)
            if len(txt) < 200:
                fail += 1
                continue
            dest.write_text(txt, encoding="utf-8")
            ok += 1
            print("   %s  %d 字" % (n, len(txt)))
        except Exception as e:
            fail += 1
        time.sleep(0.2)

    print("\n完成: 成功 %d，失败/空 %d -> %s" % (ok, fail, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
