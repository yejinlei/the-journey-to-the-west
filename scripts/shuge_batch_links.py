#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量抓取书格论坛帖子，提取短链并解码为实际网盘地址。

解码规则（来自 f.shuge.org/dl/script.js）：
  ay -> https://www.alipan.com/s/<ay>
  bd -> https://pan.baidu.com/s/<bd>?pwd=6666
  hb -> https://bw.shuge.org/@s/<hb>     （黑白版，书格直链）
  sj -> https://du.shuge.org/@s/<sj>
  yun-> https://yun.shuge.org/@s/<yun>
  hj -> https://shuge.hanjihebi.com/@s/<hj>
  dou-> https://feishu.doubao.com/drive/file/<dou>

  py -3 scripts/shuge_batch_links.py
"""
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

TOPICS = [
    ("13661", "世德堂本（已知有下载）"),
    ("136901", "关于世德堂本西游记"),
    ("7301", "求台北国图藏世德堂本胶片"),
    ("220204", "台北故宫展出的世德堂西游记"),
    ("218552", "北大藏明代内府彩绘西游记零页"),
    ("161015", "河南省图书馆公布《李卓吾批评西游记》"),
    ("149640", "李卓吾先生批评西游记（版本补充）"),
    ("186570", "求含晶子评注/怀明清抄本/李评本丙本"),
    ("10416", "《西遊證道書》日本內閣文庫"),
    ("74470", "求《通易西游正旨》"),
    ("99106", "鼎鍥全像唐三藏西游傳（朱鼎臣）"),
    ("21795", "二刻官版唐三藏西游记"),
    ("109927", "楊東來先生批評西游記"),
    ("209357", "后西游记 世业堂刊本"),
]


class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout, context=CTX).read().decode("utf-8", "replace")


def resolve_short(code):
    op = urllib.request.build_opener(NoRedir)
    req = urllib.request.Request("https://s.shuge.org/" + code, headers={"User-Agent": UA})
    try:
        r = op.open(req, timeout=25, )
        return r.headers.get("Location")
    except urllib.error.HTTPError as e:
        return e.headers.get("Location")
    except Exception:
        return None


def decode(loc):
    """从跳转 URL 的 query 里解出各网盘地址。"""
    if not loc:
        return {}
    q = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)
    out = {}
    def one(k):
        v = q.get(k, [""])[0].strip()
        return v
    if one("ay"):
        out["阿里云盘"] = "https://www.alipan.com/s/" + one("ay")
    if one("bd"):
        out["百度网盘"] = "https://pan.baidu.com/s/" + one("bd") + "?pwd=6666"
    if one("hb"):
        out["黑白版直链"] = "https://bw.shuge.org/@s/" + one("hb")
    if one("sj"):
        out["书格存储(轻)"] = "https://du.shuge.org/@s/" + one("sj")
    if one("yun"):
        out["书格存储"] = "https://yun.shuge.org/@s/" + one("yun")
    if one("hj"):
        out["书格存储2"] = "https://shuge.hanjihebi.com/@s/" + one("hj")
    if one("dou"):
        out["豆包云盘"] = "https://feishu.doubao.com/drive/file/" + one("dou")
    out["_name"] = one("n")
    return out


results = []
for tid, desc in TOPICS:
    url = "https://www.shuge.org/meet/topic/%s/" % tid
    try:
        html = get(url)
    except Exception as e:
        print("【%s】抓取失败 %s" % (tid, str(e)[:50]))
        continue
    shorts = re.findall(r"s\.shuge\.org/([A-Za-z0-9_-]{3,40})", html)
    shorts = list(dict.fromkeys(shorts))
    direct = re.findall(r"https://(?:www\.alipan\.com/s/|pan\.baidu\.com/s/)[A-Za-z0-9_-]+", html)
    print("=" * 74)
    print("【%s】%s  %s" % (tid, desc, url))
    print("  短链 %d 个: %s" % (len(shorts), ", ".join(shorts[:8])))
    if direct:
        print("  直链 %d 个" % len(direct))
        for d in sorted(set(direct))[:8]:
            kind = "阿里云盘" if "alipan" in d else "百度网盘"
            print("    %s" % d)
            results.append((tid, desc, "", kind, d))
    for code in shorts[:4]:
        loc = resolve_short(code)
        if not loc:
            print("    %s -> 无法解析" % code)
            continue
        d = decode(loc)
        name = d.pop("_name", "")
        print("    短链 %s -> %s" % (code, (name[:46] if name else "(无名)")))
        for k, v in d.items():
            print("        %-10s %s" % (k, v))
            results.append((tid, desc, name, k, v))
        time.sleep(0.6)
    time.sleep(0.6)

print("=" * 74)
print("汇总：%d 条可用链接" % len(results))
with open("book/SHUGE-LINKS.md", "w", encoding="utf-8") as f:
    f.write("# 书格论坛挖到的《西游记》相关下载链接\n\n")
    f.write("自动生成：`py -3 scripts/shuge_batch_links.py`\n\n")
    f.write("| 帖子 | 说明 | 文件 | 来源 | 链接 |\n|---|---|---|---|---|\n")
    for tid, desc, name, k, v in results:
        f.write("| %s | %s | %s | %s | %s |\n" % (tid, desc[:20], name[:36], k, v))
    f.write("\n阿里云盘需转存后不限速下载；百度网盘限速需会员；黑白版为书格直链（体积小、二值化）。\n")
print("已写入 book/SHUGE-LINKS.md")
