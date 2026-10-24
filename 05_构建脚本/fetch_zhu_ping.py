# -*- coding: utf-8 -*-
"""抓取朱鼎臣《唐三藏西游释厄传》（朱评本）67 回全文

数据源：diancang.xyz
  - 目录页: https://www.diancang.xyz/wenxueyishu/tangsancangxiyoushiezhuan/
  - 章节页: https://www.diancang.xyz/wenxueyishu/tangsancangxiyoushiezhuan/{id}.html
  - 章节 ID 连续: 70992 - 71057（共 66 章，即 67 回中的 66 回，目录页含"卷之一"卷标）

产物：
  06_文本源/diancang/txt/{chapter_id}_{title}.txt       每回清洗后纯文本
  06_文本源/diancang/raw/{chapter_id}.html               原始 HTML
  06_文本源/diancang/titles.json                          抓取清单

用法：
  python fetch_zhu_ping.py                 # 抓全部 66 章
  python fetch_zhu_ping.py --sample 3      # 抽前 3 章试抓
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "06_文本源" / "diancang"
RAW = OUT_DIR / "raw"
TXT = OUT_DIR / "txt"
RAW.mkdir(parents=True, exist_ok=True)
TXT.mkdir(parents=True, exist_ok=True)

BASE = "https://www.diancang.xyz/wenxueyishu/tangsancangxiyoushiezhuan"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 卷标映射（按 chapter_id 区间）
VOLUME_MAP = [
    (70992, 70995, "卷之一"),   # 甲集（卷之一无字）
    (70996, 71001, "卷之二"),   # 乙集
    (71002, 71009, "卷之三"),   # 丙集
    (71010, 71017, "卷之四"),   # 丁集
    (71018, 71023, "卷之五"),   # 戊集
    (71024, 71032, "卷之六"),   # 己集
    (71033, 71038, "卷之七"),
    (71039, 71041, "卷之八"),
    (71042, 71050, "卷之九"),   # 壬集
    (71051, 71057, "卷之十"),   # 癸集
]

CHAPTER_IDS = list(range(70992, 71058))  # 70992..71057 = 66 章

# 目录：chapter_id -> (chapter_no, title)
# chapter_no = 序号（1..66）；title = 章节题
TOC = {
    70992: (1, "灵根育生源流出"),
    70993: (2, "石猴投师参众仙"),
    70994: (3, "石猴修道听讲经法"),
    70995: (4, "祖师秘传悟空道"),
    70996: (5, "悟空炼兵偷器械"),
    70997: (6, "仙奏石猴扰乱三界"),
    70998: (7, "孙悟空拜授仙录"),
    70999: (8, "玉皇遣将征悟空"),
    71000: (9, "孙悟空玉封齐天大圣"),
    71001: (10, "乱蟠桃大圣偷丹反天宫诸神捉怪"),
    71002: (11, "观音赴会问原因"),
    71003: (12, "小圣施威降大圣"),
    71004: (13, "大仙助法收大圣"),
    71005: (14, "八卦炉中逃大圣"),
    71006: (15, "如来收压齐天圣"),
    71007: (16, "五行山下定心猿"),
    71008: (17, "我佛造经传极乐"),
    71009: (18, "观音奉旨往长安"),
    71010: (19, "唐太宗诏开南省"),
    71011: (20, "陈光蕊及第成婚"),
    71012: (21, "刘洪谋死陈光蕊"),
    71013: (22, "小龙王救醒陈光蕊"),
    71014: (23, "殷小姐思夫生子"),
    71015: (24, "江流和尚思报本"),
    71016: (25, "小姐嘱儿寻殷相"),
    71017: (26, "殷丞相为婿报仇"),
    71018: (27, "袁守诚妙算无私曲"),
    71019: (28, "老龙王拙计犯天条"),
    71020: (29, "太宗诏魏征救蛟龙"),
    71021: (30, "魏征弈棋斩蛟龙"),
    71022: (31, "二将军宫门镇鬼"),
    71023: (32, "唐太宗地府还魂"),
    71024: (33, "还受生唐王遵善果"),
    71025: (34, "刘全舍死进瓜果"),
    71026: (35, "刘全夫妇回阳世"),
    71027: (36, "度孤魂萧瑀正空门"),
    71028: (37, "玄奘秉诚建大会"),
    71029: (38, "观音显像化金蝉"),
    71030: (39, "唐太宗描写观音像"),
    71031: (40, "三藏起程陷虎穴"),
    71032: (41, "双叉岭伯钦留僧"),
    71033: (42, "五行山心猿归正"),
    71034: (43, "孙悟空除灭六贼"),
    71035: (44, "观音显圣赐紧箍"),
    71036: (45, "三藏授法降行者"),
    71037: (46, "蛇盘山诸神暗佑"),
    71038: (47, "孙行者降伏火龙"),
    71039: (48, "观音收伏黑妖"),
    71040: (49, "三藏收伏猪八戒"),
    71041: (50, "唐三藏被妖捉获"),
    71042: (51, "孙行者收妖救师"),
    71043: (52, "猪八戒思淫被难"),
    71044: (53, "孙行者五庄观内偷果"),
    71045: (54, "唐三藏逐去孙行者"),
    71046: (55, "唐三藏师徒被难"),
    71047: (56, "猪八戒请行者救师"),
    71048: (57, "孙悟空收妖救师"),
    71049: (58, "唐三藏师徒被妖捉"),
    71050: (59, "孙行者收伏妖魔"),
    71051: (60, "唐三藏收妖过黑河"),
    71052: (61, "观音老君收伏妖魔"),
    71053: (62, "孙行者被弥猴紊乱"),
    71054: (63, "三藏过朱紫狮驼二国"),
    71055: (64, "三藏历尽诸难已满"),
    71056: (65, "三藏见佛求经"),
    71057: (66, "唐三藏取经团圆"),
}


def get_volume(chapter_id: int) -> str:
    for lo, hi, vol in VOLUME_MAP:
        if lo <= chapter_id <= hi:
            return vol
    return "未知卷"


def fetch(url: str, retries: int = 4, timeout: int = 30) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            print(f"  [retry {i+1}/{retries}] {url[:80]} -> {e}", file=sys.stderr)
            time.sleep(2 + i * 3)
    raise RuntimeError(f"fail after {retries}: {url[:80]} ({last})")


def html_to_text(html: str) -> str:
    """从章节 HTML 抽取正文：截去页眉页脚导航"""
    # 抓 body
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S | re.I)
    body = m.group(1) if m else html
    # 去 script/style
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.S | re.I)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.S | re.I)
    # br 与块级结束 → 换行
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"</(p|div|li|h[1-6]|tr)>", "\n", body, flags=re.I)
    # 去 tag
    body = re.sub(r"<[^>]+>", "", body)
    # HTML 实体
    body = (body.replace("&nbsp;", " ").replace("&amp;", "&")
             .replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'"))
    return body


# 导航/页眉/页脚识别
NAV_EXACT = {
    "中华典藏", "留言", "专题", "人物", "书单", "风云榜",
    "字体设置", "登录", "注册", "搜索", "更多",
    "首页", "分类", "文学艺术", "文学艺术库", "小说",
    "佛教瑰宝", "佛学宝典", "儒理哲学", "历史传记", "诗词戏曲",
    "玄学五术", "学术杂记", "天文地理", "类书文集", "国学知识", "外国名著", "作家",
    "上一章", "返回目录", "下一章", "版权信息", "相关链接",
    "上一篇", "下一篇", "返回顶部", "关于我们", "联系方式",
}
NAV_RE = re.compile(r"^[（(][小中大默认][)）]\s*\d+px$|^[a-zA-Z0-9_\.\-/]+$")
FOOTER_RE = re.compile(
    r"中华典藏网旨在推广国学知识|吸取国学精华|本站非营利性站点|仅供学习|版权所有|"
    r"唐三藏西游释厄传朱鼎臣作品集"
)


def clean_chapter(text: str) -> str:
    """从整页文本中裁掉页眉/页脚，只留正文。
    优先使用 <div id="content" class="panel-body">...</div> 定位（原 HTML），
    否则回退到行级过滤。
    """
    # 优先走 HTML 结构化提取（在 fetch_chapter 里传入，这里保留行级兜底）
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]

    # 起点：跳过页眉（直到第一个"章节标题"长度 >= 6 中文的行，或首行长内容）
    start = 0
    while start < len(lines):
        ln = lines[start]
        if ln in NAV_EXACT:
            start += 1; continue
        if NAV_RE.match(ln):
            start += 1; continue
        if FOOTER_RE.search(ln):
            start += 1; continue
        if ln.endswith(".html") or ln.startswith("https?://"):
            start += 1; continue
        # 找到 CJK 长行 → 视为正文起点
        if re.search(r"[\u4e00-\u9fff]{6,}", ln):
            break
        start += 1

    # 终点：遇到"上一章"或站点标语
    end = len(lines)
    for i in range(start, len(lines)):
        ln = lines[i]
        if ln in ("上一章", "返回目录", "下一章", "上一篇", "下一篇"):
            end = i; break
        if FOOTER_RE.search(ln):
            end = i; break

    # 若起点行是章节标题，删除它（标题另存在 TOC 中，不重复）
    if start < end and len(lines[start]) <= 30 and len(lines[start]) >= 4:
        start += 1

    body = "\n".join(lines[start:end])
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def clean_chapter_from_html(html: str) -> str:
    """从原始 HTML 的 <div id="content" class="panel-body">...</div> 抽取正文，最稳。"""
    m = re.search(
        r'<div[^>]*id="content"[^>]*class="panel-body"[^>]*>(.*?)</div>\s*<div\s+class="m-page"',
        html, re.S | re.I
    )
    if not m:
        # 退而求其次：任何含 id="content" 的 div
        m = re.search(r'<div[^>]*id="content"[^>]*>(.*?)</div>', html, re.S | re.I)
    if not m:
        return ""
    inner = m.group(1)
    # 去 tag，保留 <br> 作为换行
    inner = re.sub(r"<br\s*/?>", "\n", inner, flags=re.I)
    inner = re.sub(r"</p>|</div>|</li>|</h[1-6]>", "\n", inner, flags=re.I)
    inner = re.sub(r"<[^>]+>", "", inner)
    inner = (inner.replace("&nbsp;", " ").replace("&amp;", "&")
              .replace("&lt;", "<").replace("&gt;", ">")
              .replace("&quot;", '"').replace("&#39;", "'"))
    lines = [ln.strip() for ln in inner.split("\n") if ln.strip()]
    return "\n".join(lines)


def strip_spaces_and_full_width(text: str) -> str:
    """去掉中文字符间空格，压缩空白"""
    text = text.replace("\u3000", " ")
    text = re.sub(r"[\u4e00-\u9fff] [\u4e00-\u9fff]", lambda m: m.group(0).replace(" ", ""), text)
    # 反复应用，直到稳定
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"[\u4e00-\u9fff] [\u4e00-\u9fff]", lambda m: m.group(0).replace(" ", ""), text)
    return text


def safe_filename(s: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "_", s).strip("_")[:40]


def fetch_chapter(cid: int, force: bool = False) -> dict:
    chapter_no, title = TOC[cid]
    vol = get_volume(cid)
    url = f"{BASE}/{cid}.html"
    raw_path = RAW / f"{cid}.html"
    fname = f"{cid}_{safe_filename(title)}.txt"
    txt_path = TXT / fname

    result = {
        "chapter_id": cid,
        "chapter_no": chapter_no,
        "volume": vol,
        "title": title,
        "url": url,
        "raw_path": str(raw_path.relative_to(ROOT)),
        "txt_path": str(txt_path.relative_to(ROOT)),
    }

    if txt_path.exists() and txt_path.stat().st_size > 500 and not force:
        result["status"] = "skip"
        result["chars"] = txt_path.stat().st_size
        print(f"  {chapter_no:>2}/66  skip   {title}")
        return result

    try:
        raw = fetch(url)
        html = raw.decode("utf-8", "ignore")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"  {chapter_no:>2}/66  FAIL   {title}: {e}")
        return result

    raw_path.write_bytes(raw)

    # 优先从 HTML 的 <div id="content" class="panel-body"> 精准抽取
    body = clean_chapter_from_html(html)
    if not body:
        # 兜底：文本级过滤
        text = html_to_text(html)
        body = clean_chapter(text)
    body = strip_spaces_and_full_width(body)

    if not body or len(body) < 100:
        result["status"] = "empty"
        result["chars"] = len(body)
        print(f"  {chapter_no:>2}/66  EMPTY  {title}  ({len(body)} chars)")
        return result

    txt_path.write_text(body, encoding="utf-8")
    result["status"] = "ok"
    result["chars"] = len(body)
    print(f"  {chapter_no:>2}/66  ok     {title}  {len(body)}字")
    return result


def main() -> int:
    if not sys.stdout.encoding or sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    args = sys.argv[1:]
    sample = 0
    force = False
    if "--sample" in args:
        i = args.index("--sample")
        sample = int(args[i + 1])
        args.pop(i + 1); args.pop(i)
    if "--force" in args:
        force = True
        args.remove("--force")

    targets = CHAPTER_IDS[:sample] if sample else CHAPTER_IDS
    print(f"目标: {len(targets)} 章  (70992-71057, 朱评本)")
    print(f"输出: {TXT.relative_to(ROOT)}\n")

    results = []
    for cid in targets:
        try:
            r = fetch_chapter(cid, force=force)
            results.append(r)
        except Exception as e:
            print(f"  {cid} 全失败: {e}")
            results.append({"chapter_id": cid, "status": "error", "error": str(e)})
        time.sleep(0.6)  # 温和限速

    ok = sum(1 for r in results if r.get("status") == "ok")
    skip = sum(1 for r in results if r.get("status") == "skip")
    err = sum(1 for r in results if r.get("status") in ("error", "empty"))
    total_chars = sum(r.get("chars", 0) for r in results)

    (OUT_DIR / "titles.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n=== 完成: ok={ok} skip={skip} err={err}  总字数 {total_chars} ===")
    print(f"清单: {OUT_DIR / 'titles.json'}")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
