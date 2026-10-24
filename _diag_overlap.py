"""诊断每个 key 的重合度：验证哪些是伪白话（>=0.85）。"""
import json
import re
from pathlib import Path
from hashlib import md5

TRAD_TO_SIMP = {
    '東': '东', '龍': '龙', '鳳': '凤', '漢': '汉', '經': '经', '國': '国',
    '書': '书', '讀': '读', '說': '说', '時': '时', '後': '后', '麼': '么',
    '這': '这', '們': '们', '個': '个', '頭': '头', '髮': '发', '鬚': '须',
    '見': '见', '開': '开', '關': '关', '問': '问', '題': '题', '話': '话',
    '語': '语', '誰': '谁', '過': '过', '會': '会', '於': '于', '為': '为',
    '來': '来', '去': '去', '西': '西', '南': '南', '北': '北', '門': '门',
    '學': '学', '寫': '写', '畫': '画', '中': '中', '人': '人',
}

def simp(s): return "".join(TRAD_TO_SIMP.get(c, c) for c in s)
def norm(s): return re.sub(r"[\s，。、「」『』：；？！.,:;!?()\[\]\"'\-—…～]+", "", s or "")

def overlap(text, tz):
    a = norm(tz); b = norm(simp(text))
    if not a or not b: return None
    n = min(60, len(a), len(b))
    common = sum(1 for x, y in zip(a[:n], b[:n]) if x == y)
    return common, n, common/n, a[:n], b[:n]

data = json.loads(Path("docs/data/pages/read.json").read_text(encoding="utf-8"))
mapping = json.loads(Path("_baihua_mapping.json").read_text(encoding="utf-8"))

lines = data["lines"]
# find original text by key
key2text = {}
for l in lines:
    if l.get("edition") != "gubao": continue
    txt = l.get("text", "") or ""
    k = l["page_id"] + "#" + md5(txt[:20].encode()).hexdigest()[:8]
    key2text[k] = txt

fakes = []
ok = []
for k, tz in mapping.items():
    if k not in key2text: 
        print("MISS:", k); continue
    text = key2text[k]
    r = overlap(text, tz)
    if r is None:
        continue
    common, n, ratio, a, b = r
    if ratio >= 0.85:
        fakes.append((k, ratio, common, n, text[:120], tz[:120]))
    else:
        ok.append((k, ratio))

print(f"OK ({len(ok)}):")
for k, r in ok: print(f"  {k}  ratio={r:.3f}")
print(f"\nFAKE ({len(fakes)}):")
for k, ratio, common, n, t, tz in fakes:
    print(f"\n=== {k}  ratio={ratio:.3f}  common={common}/{n} ===")
    print(f"  TEXT[:120]: {t}")
    print(f"  TZ  [:120]: {tz}")
