"""检查 gubao 第 100 回白话文是否与繁体相同（疑似未翻译）。"""
import json
from pathlib import Path

d = json.loads(Path("docs/data/pages/read.json").read_text(encoding="utf-8"))
lines = d["lines"]

# 常见繁体字（简体版本中不应出现）
TRAD_SET = set(
    "東龍鳳漢經國書讀說時後麼這們個頭髮鬚見開關問題話語誰個過個個個個個個個個個個個個個個個"
    "東龍鳳漢經國書讀說時後麼這們個頭髮鬚見開關問題話語誰個過個個個個個個個個個個個個個個個個個個"
    "東龍鳳漢經國書讀說時後麼這們個頭髮鬚見開關問題話語誰個過個個個個個個個個個個個個個個個個個個個個個個個個"
)
# 用明确的方式定义繁体字集
TRAD_SET = set([
    "東", "龍", "鳳", "漢", "經", "國", "書", "讀", "說", "時",
    "後", "麼", "這", "們", "個", "頭", "髮", "鬚", "見", "開",
    "關", "問", "題", "話", "語", "誰", "過", "會", "於", "為",
    "來", "去", "東", "西", "南", "北", "東", "門", "開", "關",
    "國", "學", "問", "題", "話", "說", "讀", "寫", "書", "畫",
    "東", "西", "南", "北", "中", "國", "漢", "人", "個", "們",
    "東", "龍", "鳳", "漢", "經", "國", "書", "讀", "說", "時",
    "後", "麼", "這", "們", "個", "頭", "髮", "鬚", "見", "開",
    "關", "問", "題", "話", "語", "誰", "過", "會", "於", "為",
])

def count_trad(s: str) -> int:
    return sum(1 for c in s if c in TRAD_SET)

gb = [l for l in lines if l.get("edition") == "gubao"]
ch100 = [l for l in gb if l["page_id"].startswith("gubao#c100")]

print(f"gubao total lines: {len(gb)}")
print(f"gubao c100 lines: {len(ch100)}")
print()

bad_lines = []
for l in ch100:
    tz = l.get("text_zh", "") or ""
    n_trad = count_trad(tz)
    if n_trad > 0:
        bad_lines.append((l["form_type"], n_trad, tz[:80]))

print(f"=== gubao c100 中 text_zh 仍含繁体字的行数: {len(bad_lines)} / {len(ch100)} ===")
for ft, n, s in bad_lines[:20]:
    print(f"  [{ft}] trad={n} | {s}")

print()
print("=== gubao c100 前 10 行对比 ===")
for l in ch100[:10]:
    t = l.get("text", "")
    tz = l.get("text_zh", "")
    same = "SAME" if t == tz else "DIFF"
    print(f"[{l['form_type']}] {same} | trad={count_trad(tz)}")
    print(f"  text   : {t[:120]}")
    print(f"  text_zh: {tz[:120]}")
    print()

# 检查所有 edition 是否有类似情况
print("=== 各 edition c100 情况 ===")
for ed in ["gubao", "shidetang", "baihui_xiangzhu", "zhu_ping", "xu_xiyouji", "hou_xiyouji"]:
    ch = [l for l in lines if l.get("edition") == ed and l["page_id"].startswith(ed + "#c100")]
    if not ch:
        print(f"  {ed}: c100 not found")
        continue
    bad = sum(1 for l in ch if count_trad(l.get("text_zh", "") or "") > 0)
    print(f"  {ed} c100: {len(ch)} lines, {bad} with trad chars")
