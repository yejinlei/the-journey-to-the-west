"""导出 53 行伪白话的详细清单。"""
import json
import re
from pathlib import Path

d = json.loads(Path("docs/data/pages/read.json").read_text(encoding="utf-8"))
lines = d["lines"]
gb = [l for l in lines if l.get("edition") == "gubao"]

TRAD_TO_SIMP = {
    '東':'东', '龍':'龙', '鳳':'凤', '漢':'汉', '經':'经', '國':'国',
    '書':'书', '讀':'读', '說':'说', '時':'时', '後':'后', '麼':'么',
    '這':'这', '們':'们', '個':'个', '頭':'头', '髮':'发', '鬚':'须',
    '見':'见', '開':'开', '關':'关', '問':'问', '題':'题', '話':'话',
    '語':'语', '誰':'谁', '過':'过', '會':'会', '於':'于', '為':'为',
    '來':'来', '門':'门', '學':'学', '寫':'写', '畫':'画',
}

def simp_from_trad(s):
    return "".join(TRAD_TO_SIMP.get(c, c) for c in s)

def norm(s):
    return re.sub(r"[\s，。、「」『』：；？！.,:;!?()\[\]\"'\-—…～]+", "", s)

def is_fake(l):
    txt = l.get("text", "") or ""
    tz = l.get("text_zh", "") or ""
    if not txt or not tz:
        return False
    a = norm(tz)
    b = norm(simp_from_trad(txt))
    if not b:
        return False
    p = min(60, len(a), len(b))
    common = sum(1 for x, y in zip(a[:p], b[:p]) if x == y)
    return (common / max(p, 1)) >= 0.85

fakes = [l for l in gb if is_fake(l)]
print(f"共 {len(fakes)} 行伪白话")
print()
for i, l in enumerate(fakes):
    print(f"--- [{i+1}] {l['page_id']} (form_type={l.get('form_type')}) ---")
    print(f"原文: {l.get('text','')}")
    print(f"现zh: {l.get('text_zh','')}")
    print()
