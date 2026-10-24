"""导出 53 行伪白话的唯一键 + 原文，用于 AI 生成译文时精准对齐。"""
import json, re
from pathlib import Path
from hashlib import md5

d = json.loads(Path("docs/data/pages/read.json").read_text(encoding="utf-8"))
lines = d["lines"]
gb = [l for l in lines if l.get("edition") == "gubao"]

# 复用 _scan_gubao_fake.py 的伪白话判定
TRAD_TO_SIMP = {
    '東':'东','龍':'龙','鳳':'凤','漢':'汉','經':'经','國':'国','書':'书','讀':'读','說':'说',
    '時':'时','後':'后','麼':'么','這':'这','們':'们','個':'个','頭':'头','髮':'发','鬚':'须',
    '見':'见','開':'开','關':'关','問':'问','題':'题','話':'话','語':'语','誰':'谁','過':'过',
    '會':'会','於':'于','為':'为','來':'来','門':'门','學':'学','寫':'写','畫':'画',
}
TRAD_SET = {k for k,v in TRAD_TO_SIMP.items() if k != v}

def simp_from_trad(s):
    return "".join(TRAD_TO_SIMP.get(c,c) for c in s)

def is_title_or_poem(l):
    ft = l.get("form_type","")
    if ft in ("title","poem","poem_start","poem_end","couplet"):
        return True
    return False

def norm(s):
    return re.sub(r"[\s，。、「」『』：；？！.,:;!?()\[\]\"'\-—…～]+","",s)

def is_fake(l):
    if is_title_or_poem(l):
        return False
    txt = l.get("text","") or ""
    tz = l.get("text_zh","") or ""
    if not tz or len(txt) < 10:
        return False
    a = norm(tz)
    b = norm(simp_from_trad(txt))
    if not b:
        return False
    prefix_len = min(60, len(a), len(b))
    common = sum(1 for x,y in zip(a[:prefix_len], b[:prefix_len]) if x==y)
    return common/max(prefix_len,1) >= 0.85

fakes = [l for l in gb if is_fake(l)]
print(f"fake count: {len(fakes)}")

# 用 page_id + md5(原文前20字) 做唯一 key
out = []
for l in fakes:
    pid = l["page_id"]
    txt = l.get("text","") or ""
    key = pid + "#" + md5(txt[:20].encode("utf-8")).hexdigest()[:8]
    out.append({
        "key": key,
        "page_id": pid,
        "form_type": l.get("form_type",""),
        "char_count": l.get("char_count",0),
        "text_len": len(txt),
        "text": txt,
    })

# 写文件
Path("_fake_keys.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("written _fake_keys.json, entries:", len(out))

# 也打印一份极简版供查看
for i,o in enumerate(out,1):
    print(f"\n--- [{i}] {o['key']} (len={o['text_len']}) ---")
    print(o["text"])
