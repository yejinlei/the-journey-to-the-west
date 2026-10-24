#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取书格论坛指定帖子，去掉脚本后输出正文与外链。

  py -3 scripts/fetch_shuge_topic.py 13661
"""
import re
import ssl
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

topic = sys.argv[1] if len(sys.argv) > 1 else "13661"
url = "https://www.shuge.org/meet/topic/%s/" % topic

req = urllib.request.Request(url, headers={"User-Agent": UA})
html = urllib.request.urlopen(req, timeout=30, context=CTX).read().decode("utf-8", "replace")

# 去掉 script / style
clean = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
clean = re.sub(r"<style[^>]*>.*?</style>", " ", clean, flags=re.S | re.I)
txt = re.sub(r"<[^>]+>", "\n", clean)
txt = re.sub(r"\n{2,}", "\n", txt)
lines = [l.strip() for l in txt.split("\n") if len(l.strip()) > 2]

# 只输出含关键内容的行，跳过导航菜单
SKIP = ("首页", "资源集", "经部", "史部", "子部", "集部", "丛书", "绘画", "书法",
        "碑拓", "舆图", "影像", "哲学类", "宗教", "科学类", "社会科学类", "史地",
        "语言文学类", "艺术类", "专题系列", "宋刻本", "永乐大典", "中医典籍",
        "CC0", "硬盘直递", "自寄硬盘", "售后服务", "交流区", "问询资源",
        "资源分享", "文献研读", "文献情报", "站务反馈", "bookget专区",
        "技术交流", "水乐园", "书格动态", "学术动态", "展览动态", "捐赠",
        "致谢", "关于", "标识使用", "搜索", "菜单", "function", "var ",
        "document", "window", "if (!", "window.")

out = []
for l in lines:
    if any(l.startswith(s) for s in SKIP) or len(l) > 400:
        continue
    if any(k in l for k in ("function", "var ", "document.", "window.")):
        continue
    out.append(l)

print("=" * 72)
print("帖子 %s" % url)
print("=" * 72)
for l in out[:90]:
    print("  " + l[:150])

print("\n" + "=" * 72)
print("外链：")
links = re.findall(r"href=[\"']([^\"']+)[\"']", html)
KEY = ("pan.baidu", "aliyundrive", "alipan", "drive.google", "archive.org",
       "mega.nz", "weiyun", "lanzou", "123pan", "quark", "docs.qq",
       "shuge.org/ebook", "shuge.org/view", ".pdf", ".zip", ".rar", "uploads")
ext = sorted(set(l for l in links if any(k in l for k in KEY)))
for l in ext[:30]:
    print("  " + l)
print("  共 %d 条" % len(ext))
