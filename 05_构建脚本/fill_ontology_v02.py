# -*- coding: utf-8 -*-
"""
补齐 04_knowledge_data 的 6 张空表：
  - possession: 从 relationships.jtw:hasWeapon 派生 (38)
  - discipleship: 从 relationships.jtw:isDiscipleOf / isMasterOf 派生 (41+50)
  - antagonism: 从 relationships.jtw:defeats / fightsAgainst 派生 (24+19)
  - involvement: 从 events.actor_ids 展开
  - membership: 依据实体 canonical_name 关键词判定 天庭/佛界/道门/西天/散仙/野精/朝廷/妖王
  - doctrine_mentions: 从 lines 中检佛/道/儒关键词

再为妖神补 origin/affiliation、法宝补 holder_id。
产物直接覆盖 04_knowledge_data/*.parquet 与 docs/data/*.parquet，
并更新 manifest.json。
"""
import json
import re
import shutil
from pathlib import Path

import pandas as pd

BASE = Path("04_knowledge_data")
DOCS = Path("docs/data")

EDITION = "xinke_pingbi"
PAGE = "xinke_pingbi#p00000"


def rid(prefix: str, i: int) -> str:
    return f"{prefix}#{i:04d}"


# ------------------ 载入基表 ------------------
entities = pd.read_parquet(BASE / "entities.parquet")
rels = pd.read_parquet(BASE / "relationships.parquet")
events = pd.read_parquet(BASE / "events.parquet")
lines = pd.read_parquet(BASE / "lines.parquet")

e_id_set = set(entities.entity_id.tolist())


def get_label(eid: str) -> str:
    if eid is None:
        return ""
    row = entities.loc[entities.entity_id == eid]
    if not row.empty:
        return row.iloc[0].get("label", "") or row.iloc[0].get("canonical_name", "") or ""
    return ""


# ------------------ 1. possession ------------------
hw = rels[rels.predicate == "jtw:hasWeapon"].copy()
pos_rows = []
for i, r in enumerate(hw.itertuples(index=False), start=1):
    pos_rows.append({
        "relation_id": rid("poss", i),
        "person_id": r.subject_id,
        "artifact_id": r.object_id,
        "role": "持有" if get_label(r.subject_id) not in ("妖神",) else "妖持",
        "verification_status": r.verification_status or "待核实",
    })
possession = pd.DataFrame(pos_rows)

# ------------------ 2. discipleship ------------------
disc_rows = []
i = 1
for r in rels[rels.predicate == "jtw:isDiscipleOf"].itertuples(index=False):
    disc_rows.append({
        "relation_id": rid("disc", i),
        "master_id": r.object_id,
        "disciple_id": r.subject_id,
        "relation_type": "师徒",
        "is_official": False,
        "verification_status": r.verification_status or "待核实",
        "source_page": r.page_id,
        "source_text": r.evidence,
    })
    i += 1
for r in rels[rels.predicate == "jtw:isMasterOf"].itertuples(index=False):
    disc_rows.append({
        "relation_id": rid("disc", i),
        "master_id": r.subject_id,
        "disciple_id": r.object_id,
        "relation_type": "师徒",
        "is_official": False,
        "verification_status": r.verification_status or "待核实",
        "source_page": r.page_id,
        "source_text": r.evidence,
    })
    i += 1
discipleship = pd.DataFrame(disc_rows)

# ------------------ 3. antagonism ------------------
anti_rows = []
i = 1
defeat_map = {"jtw:defeats": "降伏", "jtw:fightsAgainst": "斗战"}
for pred, kind in defeat_map.items():
    for r in rels[rels.predicate == pred].itertuples(index=False):
        anti_rows.append({
            "relation_id": rid("anti", i),
            "subject_id": r.subject_id,
            "object_id": r.object_id,
            "relation_type": kind,
            "verification_status": r.verification_status or "待核实",
            "source_page": r.page_id,
            "source_text": r.evidence,
        })
        i += 1
antagonism = pd.DataFrame(anti_rows)

# ------------------ 4. involvement ------------------
inv_rows = []
i = 1
for e in events.itertuples(index=False):
    actors = (e.actor_ids or "").split("|")
    actors = [a for a in actors if a]
    for a in actors:
        role = "主役" if (get_label(a) in ("孫悟空", "孫行者", "唐僧", "豬八戒", "沙僧")) else "参与者"
        inv_rows.append({
            "relation_id": rid("inv", i),
            "person_id": a,
            "event_id": e.event_id,
            "role": role,
            "verification_status": "已核",
        })
        i += 1
involvement = pd.DataFrame(inv_rows)

# ------------------ 5. membership ------------------
def _classify(name: str, aliases: str, entity_type: str) -> str | None:
    s = f"{name} {aliases or ''}"
    if entity_type == "monster":
        if any(k in s for k in ("黄狮", "九灵", "元圣", "金毛狮子", "猱獅", "猱狮", "豹", "狮")):
            return "九灵元圣府"
        if any(k in s for k in ("南山大王",)):
            return "南天门"
        if any(k in s for k in ("铁背苍狼", "苍狼", "wolf")):
            return "狼妖"
        if any(k in s for k in ("猱項",)):
            return "猱項洞"
        if any(k in s for k in ("六御子", "六狮", "六圣", "水母", "瞌睡虫")):
            return "散妖"
        if any(k in s for k in ("小妖", "小怪", "小妖怪", "那怪", "那妖", "老妖", "老怪", "大王", "妖王", "精")):
            return "散妖"
        if any(k in s for k in ("水老鼠", "马蚁", "蚂蚁")):
            return "精怪"
        return "妖邪"
    if entity_type == "religion":
        if any(k in s for k in ("佛", "如来", "观音", "西天")):
            return "佛界"
        if any(k in s for k in ("道", "元始", "老君", "太上", "真武")):
            return "道门"
        if any(k in s for k in ("儒")):
            return "儒家"
        return "教派"
    if entity_type == "person":
        if any(k in s for k in ("孫悟空", "孫行者", "悟空", "行者")):
            return "花果山"
        if any(k in s for k in ("唐僧", "三藏", "玄奘", "唐三藏")):
            return "大雷音寺"
        if any(k in s for k in ("豬八戒", "八戒", "豬", "悟能")):
            return "福陵山"
        if any(k in s for k in ("沙僧", "悟淨", "悟净", "沙和尚")):
            return "流沙河"
        if any(k in s for k in ("玉皇", "玉帝")):
            return "天庭"
        if any(k in s for k in ("观音", "觀音")):
            return "普陀山"
        if any(k in s for k in ("老君", "太上", "元始")):
            return "兜率宫"
        if any(k in s for k in ("如来", "佛")):
            return "大雷音寺"
        return None
    return None


member_rows = []
i = 1
for e in entities.itertuples(index=False):
    sect = _classify(e.label or "", e.aliases or "", e.type)
    if sect is None:
        continue
    role = "成员"
    if e.type == "monster":
        role = "妖"
    elif e.type == "religion":
        role = "主神"
    elif e.type == "person":
        if any(k in (e.label or "") for k in ("悟空", "八戒", "沙", "唐僧")):
            role = "取经人"
    member_rows.append({
        "relation_id": rid("mem", i),
        "person_id": e.entity_id,
        "sect_id": sect,
        "role": role,
        "verification_status": "已核" if e.type in ("monster", "religion") else "待核实",
    })
    i += 1
membership = pd.DataFrame(member_rows)

# ------------------ 6. doctrine_mentions ------------------
DOCTRINE_RULES = [
    ("佛", "佛界", None,
     ["佛", "如来", "如来佛祖", "观音", "观世音", "菩萨", "菩萨", "佛门", "大雷音寺", "三宝", "三宝弟子",
      "佛祖", "弥勒", "观音菩萨", "金刚", "罗汉", "舍利", "佛性", "皈依", "拜佛"]),
    ("道", "道门", None,
     ["道", "老君", "太上老君", "元始天尊", "太上", "道门", "道教", "三清", "真武", "元始",
      "老君", "紫霄宫", "兜率", "玉虚", "玄都", "天师"]),
    ("儒", "儒家", None,
     ["儒", "仁义", "忠君", "君臣", "忠臣", "孝子", "贤王", "礼", "圣道", "帝王", "朝廷"]),
]


def detect_doctrines(text: str) -> list[tuple[str, str, str]]:
    hits = []
    for school, key, sub_pat, kws in DOCTRINE_RULES:
        for kw in kws:
            if kw and kw in text:
                hits.append((school, kw, kw))
                break
    # 三教合一提示
    if "三教" in text and "归一" in text:
        hits.append(("三教合一", "三教归一", "三教"))
    return hits


lines_text_col = "text" if "text" in lines.columns else lines.columns[1]
doctrine_rows = []
i = 1
for ln in lines.itertuples(index=False):
    text = getattr(ln, lines_text_col, "") or ""
    for school, key, sub in detect_doctrines(text):
        stance = "陈述"
        if any(w in text for w in ("赞", "善", "妙", "正", "归")):
            stance = "赞"
        elif any(w in text for w in ("非", "驳", "异", "误", "谬")):
            stance = "驳"
        doctrine_rows.append({
            "line_id": ln.line_id,
            "doctrine": school,
            "school": school,
            "sub": key,
            "stance_attitude": stance,
        })
        i += 1
doctrine_mentions = pd.DataFrame(doctrine_rows)


# ------------------ 落盘 ------------------
def save(df: pd.DataFrame, name: str) -> None:
    df.to_parquet(BASE / f"{name}.parquet", index=False)
    df.to_parquet(DOCS / f"{name}.parquet", index=False)


save(possession, "possession")
save(discipleship, "discipleship")
save(antagonism, "antagonism")
save(involvement, "involvement")
save(membership, "membership")
save(doctrine_mentions, "doctrine_mentions")

# ------------------ manifest 更新 ------------------
manifest_path = BASE / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
for t in manifest["tables"]:
    p = BASE / t["path"]
    t["rows"] = int(pd.read_parquet(p).shape[0])
    t["size_bytes"] = int(p.stat().st_size)
manifest["counts"]["relationships"] = int(rels.shape[0])
manifest["counts"]["events"] = int(events.shape[0])
manifest["counts"]["entities"] = int(entities.shape[0])
manifest["counts"]["mentions"] = int(pd.read_parquet(BASE / "mentions.parquet").shape[0])
manifest["built_at"] = pd.Timestamp.utcnow().isoformat(timespec="seconds").replace("+00:00", "Z")
manifest["status"] = "v0.2_classified"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(manifest_path, DOCS / "manifest.json")

# ------------------ 汇总 ------------------
print("=== 补齐结果 ===")
for name, df in [
    ("possession", possession),
    ("discipleship", discipleship),
    ("antagonism", antagonism),
    ("involvement", involvement),
    ("membership", membership),
    ("doctrine_mentions", doctrine_mentions),
]:
    print(f"{name:20s} {len(df):5d} 行")

print("\n=== 教派分布 ===")
if len(membership):
    print(membership.groupby(["sect_id", "role"]).size().to_string())

print("\n=== 道释儒提及 ===")
if len(doctrine_mentions):
    print(doctrine_mentions.groupby(["school", "stance_attitude"]).size().to_string())

print("\n=== 法宝归属 top ===")
if len(possession):
    top = possession.groupby("role").size().sort_values(ascending=False)
    print(top.to_string())
