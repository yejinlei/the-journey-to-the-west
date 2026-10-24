"""扫描 gubao 全书：区分 真白话 / 伪白话（仅繁→简） / 保留原文（诗、标题）。"""
import json
import re
from pathlib import Path

d = json.loads(Path("docs/data/pages/read.json").read_text(encoding="utf-8"))
lines = d["lines"]
gb = [l for l in lines if l.get("edition") == "gubao"]

# 常见繁体→简体字（判断 text_zh 是否只是繁→简）
TRAD_TO_SIMP = {
    '東':'东', '龍':'龙', '鳳':'凤', '漢':'汉', '經':'经', '國':'国',
    '書':'书', '讀':'读', '說':'说', '時':'时', '後':'后', '麼':'么',
    '這':'这', '們':'们', '個':'个', '頭':'头', '髮':'发', '鬚':'须',
    '見':'见', '開':'开', '關':'关', '問':'问', '題':'题', '話':'话',
    '語':'语', '誰':'谁', '過':'过', '會':'会', '於':'于', '為':'为',
    '來':'来', '去':'去', '西':'西', '南':'南', '北':'北', '門':'门',
    '學':'学', '寫':'写', '畫':'画', '中':'中', '人':'人',
}
# 只保留真正繁→简不同的（有些字繁简一样）
TRAD_SET = {k for k, v in TRAD_TO_SIMP.items() if k != v}


def simp_from_trad(s: str) -> str:
    """把繁体字符串逐字替换成简体，仅对已知字生效。"""
    return "".join(TRAD_TO_SIMP.get(c, c) for c in s)


def is_title_or_poem(l):
    """标题/诗歌行不参与白话判定。"""
    ft = l.get("form_type", "")
    if ft in ("title", "poem", "poem_start", "poem_end", "couplet"):
        return True
    txt = l.get("text", "") or ""
    if txt.startswith("第一") or txt.startswith("第二"):
        return True
    return False


stats = {
    "total": 0,
    "title_or_poem": 0,
    "pure_simplified": 0,  # text_zh 与 simp(text) 高度一致 → 伪白话
    "real_rewritten": 0,   # text_zh 与 simp(text) 有明显差异 → 真白话
    "empty_or_missing": 0,
    "sample_pure": [],
    "sample_real": [],
}

per_chapter = {}

for l in gb:
    stats["total"] += 1
    txt = l.get("text", "") or ""
    tz = l.get("text_zh", "") or ""
    pid = l["page_id"]
    m = re.search(r"c(\d+)", pid)
    chap = m.group(1) if m else "?"

    per_chapter.setdefault(chap, {"total": 0, "pure": 0, "real": 0, "title": 0})
    per_chapter[chap]["total"] += 1

    if is_title_or_poem(l):
        stats["title_or_poem"] += 1
        per_chapter[chap]["title"] += 1
        continue

    if not tz:
        stats["empty_or_missing"] += 1
        continue

    # 把原文 text 逐字繁→简
    t_simp = simp_from_trad(txt)

    # 计算 text_zh 与 t_simp 的相似度（去除标点后的差异率）
    def norm(s):
        s = re.sub(r"[\s，。、「」『』：；？！.,:;!?()\[\]\"'\-—…～]+", "", s)
        return s

    a = norm(tz)
    b = norm(t_simp)
    if not b:
        stats["empty_or_missing"] += 1
        continue

    # 用 Levenshtein-ish：字符差
    # 若 text_zh 与 text_simp 前 60 字几乎相同 → 伪白话
    prefix_len = min(60, len(a), len(b))
    common = sum(1 for x, y in zip(a[:prefix_len], b[:prefix_len]) if x == y)
    ratio = common / max(prefix_len, 1)

    # 另外看：是否只用了少量繁体字（若原文本已简化，则 trad=0 也合法）
    # 判定：ratio >= 0.85 视为伪白话（句式相同，仅字差异）
    if ratio >= 0.85:
        stats["pure_simplified"] += 1
        per_chapter[chap]["pure"] += 1
        if len(stats["sample_pure"]) < 3:
            stats["sample_pure"].append((chap, txt[:80], tz[:80]))
    else:
        stats["real_rewritten"] += 1
        per_chapter[chap]["real"] += 1
        if len(stats["sample_real"]) < 3:
            stats["sample_real"].append((chap, txt[:80], tz[:80]))

print(f"=== gubao 全书 {stats['total']} 行分类 ===")
for k, v in stats.items():
    if k.startswith("sample"):
        continue
    print(f"  {k}: {v}")
print()

print("=== 伪白话样本（3 例） ===")
for c, t, tz in stats["sample_pure"]:
    print(f"  [ch{c}]")
    print(f"    原文: {t}")
    print(f"    现zh: {tz}")
print()
print("=== 真白话样本（3 例） ===")
for c, t, tz in stats["sample_real"]:
    print(f"  [ch{c}]")
    print(f"    原文: {t}")
    print(f"    现zh: {tz}")
print()

print("=== 按回统计：伪白话/真白话/标题 ===")
print(f"{'chap':>4} {'total':>5} {'title':>5} {'pure':>5} {'real':>5}")
for c in sorted(per_chapter.keys(), key=lambda x: int(x) if x.isdigit() else 0):
    s = per_chapter[c]
    print(f"{c:>4} {s['total']:>5} {s['title']:>5} {s['pure']:>5} {s['real']:>5}")
