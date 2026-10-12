#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量探测古籍/汉籍数字资源站点的可达性。

  py -3 scripts/probe_sources4.py
"""
import sys
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# (分组, 站点名, URL)
SITES = [
    ("日本", "早稻田大学图书馆", "https://www.wul.waseda.ac.jp/"),
    ("日本", "早稻田 古典籍総合DB", "https://www.wul.waseda.ac.jp/kotenseki/"),
    ("日本", "京都大学貴重資料", "https://rmda.kulib.kyoto-u.ac.jp/"),
    ("日本", "東京大学デジタルアーカイブ", "https://da.dl.itc.u-tokyo.ac.jp/"),
    ("日本", "国立国会図書館", "https://dl.ndl.go.jp/"),
    ("日本", "国立国会図書館サーチ", "https://ndlsearch.ndl.go.jp/"),
    ("日本", "国立公文書館", "https://digital.archives.go.jp/"),
    ("日本", "東洋文庫", "https://www.toyo-bunko.or.jp/"),
    ("日本", "名古屋市蓬左文庫", "https://www.city.nagoya.jp/"),
    ("欧美", "Harvard Library Viewer", "https://iiif.lib.harvard.edu/"),
    ("欧美", "Harvard HOLLIS", "https://hollis.harvard.edu/"),
    ("欧美", "Harvard NRS", "https://nrs.harvard.edu/"),
    ("欧美", "Princeton", "https://library.princeton.edu/"),
    ("欧美", "LOC 美国国会", "https://www.loc.gov/"),
    ("欧美", "HathiTrust", "https://babel.hathitrust.org/"),
    ("欧美", "Michigan", "https://quod.lib.umich.edu/"),
    ("欧美", "Internet Archive", "https://archive.org/"),
    ("欧美", "Google Books", "https://books.google.com/"),
    ("欧美", "柏林国家图书馆", "https://digital.staatsbibliothek-berlin.de/"),
    ("两岸", "台湾國家圖書館古籍影像", "https://rbook.ncl.edu.tw/"),
    ("两岸", "台湾國圖", "https://www.ncl.edu.tw/"),
    ("两岸", "中研院史语所傅斯年圖書館", "https://lib.ihp.sinica.edu.tw/"),
    ("两岸", "中华古籍资源库", "https://read.nlc.cn/"),
    ("两岸", "国家图书馆", "https://www.nlc.cn/"),
    ("两岸", "CADAL", "https://cadal.edu.cn/"),
    ("两岸", "书格", "https://www.shuge.org/"),
    ("两岸", "国学大师", "https://www.guoxuedashi.net/"),
    ("两岸", "殆知阁", "http://www.daizhige.org/"),
    ("两岸", "中国哲学书电子化计划", "https://ctext.org/"),
    ("两岸", "维基文库", "https://zh.wikisource.org/"),
]


def probe(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, int((time.time() - t) * 1000)
    except Exception as e:
        msg = str(e)
        if "403" in msg:
            return 403, int((time.time() - t) * 1000)
        return msg[:38], int((time.time() - t) * 1000)


def main():
    print("%-6s %-26s %-30s %s" % ("分组", "站点", "结果", "耗时"))
    print("-" * 78)
    good = []
    for grp, name, url in SITES:
        st, ms = probe(url)
        ok = (st == 200)
        print("%-6s %-26s %-30s %dms" % (grp, name, str(st), ms))
        if ok:
            good.append((grp, name, url))
        time.sleep(0.3)
    print("-" * 78)
    print("可达（200）的站点：")
    for grp, name, url in good:
        print("  [%s] %s  %s" % (grp, name, url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
