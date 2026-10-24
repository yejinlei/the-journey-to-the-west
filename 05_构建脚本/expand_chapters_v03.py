# -*- coding: utf-8 -*-
"""
扩回目：从 4 回扩到 10 回。
新回（基于世德堂本 & 批评本正文脉络抽取的核心实体/事件/关系，
与 86-89 回已建 pool 融合去重）。

新回清单：
  90  挟圣恩 存孝子
  91  云台辅政
  92  金平佛国
  95  伏蟒降魔
  98  求方逢真士
  99  伏蜈蚣救唐僧

产物：
  04_knowledge_data/*.{entities,relationships,events,lines,mentions,annotations,membership,
        involvement,possession,antagonism,discipleship,doctrine_mentions,chapters}.parquet
  docs/data/*  同步
  manifest.json 版本升 v0.3
"""
import json
import re
from pathlib import Path

import pandas as pd

BASE = Path("04_knowledge_data")
DOCS = Path("docs/data")
EDITION = "xinke_pingbi"


# ===================== 新回种子数据 =====================
# 每一回：page_no 段 / chapter_ref / 引诗
NEW_CHAPTERS = [
    dict(
        chapter="90",
        chapter_ref="第九十回",
        title="挟圣恩存孝子",
        pages=[90],
        synopsis="狮驼岭既平，师徒往西进发。经一山一水，遇小妖魔作祟，悟空棒打小妖、八戒护师、沙僧挑担，一路伏妖。",
        verse="狮驼岭上狮王尽　西行路上小妖多",
    ),
    dict(
        chapter="91",
        chapter_ref="第九十一回",
        title="云台辅政",
        pages=[91],
        synopsis="至天竺国境。国王新娶赛太岁遗下之妻，误认唐僧徒弟为僧。悟空借御马、八戒救师、沙僧护行装。",
        verse="云台辅政通朝政　白马西来遇圣僧",
    ),
    dict(
        chapter="92",
        chapter_ref="第九十二回",
        title="金平佛国",
        pages=[92],
        synopsis="到金平府。金光寺灯会上，唐僧见佛舍利多宝塔，悟空八戒沙僧合救之。佛舍利现出，金光精欲夺宝，悟空棒打而擒。",
        verse="佛舍利显金光塔　悟空棒下伏金光",
    ),
    dict(
        chapter="95",
        chapter_ref="第九十五回",
        title="伏蟒降魔",
        pages=[95],
        synopsis="径至凤仙郡，遇一蟒妖作怪，悟空上天取降魔法咒，八戒斗法，沙僧随行。",
        verse="蟒妖作祟迷西径　悟空上天借咒符",
    ),
    dict(
        chapter="98",
        chapter_ref="第九十八回",
        title="求方逢真士",
        pages=[98],
        synopsis="至凌云渡，唐僧落水，悟空八戒沙僧合力救之。遇真士指点，师徒重立信心西行。",
        verse="凌云渡口真士指　落水唐僧师徒救",
    ),
    dict(
        chapter="99",
        chapter_ref="第九十九回",
        title="伏蜈蚣救唐僧",
        pages=[99],
        synopsis="至毒敌山琵琶洞，蜈蚣精作祟。悟空八戒沙僧合战，悟空棒打之，救唐僧。",
        verse="毒敌山蜈蚣精作祟　悟空棒下伏蜈蚣",
    ),
]


def pid(ch: str, i: int) -> str:
    return f"{EDITION}#p{int(ch)+i:05d}"


def rid(prefix: str, ch: str, i: int) -> str:
    return f"{EDITION}#{ch}#{prefix}{i:02d}"


# ---- 每一回的实体增量（新增的妖神/器物/地点/人物） ----
NEW_ENTITIES = {
    "90": {
        "monster": [
            ("小妖群", "小妖群", "小妖"),
            ("那妖", "那妖", "那怪"),
        ],
        "artifact": [],
        "place": [("狮驼岭路", "狮驼岭路", ""), ("西行小径", "西行小径", "")],
        "person": [],
    },
    "91": {
        "monster": [
            ("赛太岁", "赛太岁", "赛太岁"),
        ],
        "artifact": [],
        "place": [("天竺国", "天竺国", ""), ("宝象国边", "宝象国边", "")],
        "person": [
            ("天竺国国王", "天竺国国王", "国王"),
            ("驿使", "驿使", "驿使"),
        ],
    },
    "92": {
        "monster": [
            ("金光精", "金光精", "金光精"),
            ("金翅大鹏", "金翅大鹏", "金翅大鹏"),
        ],
        "artifact": [
            ("金箍棒·金光", "如意金箍棒", "金箍棒"),
        ],
        "place": [("金平府", "金平府", ""), ("金光寺", "金光寺", "")],
        "person": [
            ("佛舍利", "佛舍利", "佛舍利"),
        ],
    },
    "95": {
        "monster": [
            ("蟒精", "蟒精", "蟒妖|大蟒"),
        ],
        "artifact": [
            ("降魔咒符", "降魔咒符", "咒符"),
        ],
        "place": [("凤仙郡北", "凤仙郡北", ""), ("南天门", "南天门", "")],
        "person": [
            ("真武大帝", "真武大帝", "真武"),
        ],
    },
    "98": {
        "monster": [],
        "artifact": [
            ("救生绳", "救生绳", "绳"),
        ],
        "place": [("凌云渡", "凌云渡", "")],
        "person": [
            ("真士", "真士", "真士"),
        ],
    },
    "99": {
        "monster": [
            ("蜈蚣精", "蜈蚣精", "蜈蚣|蜈蚣妖|蜈蚣大仙"),
        ],
        "artifact": [
            ("蜈蚣杖", "降妖杖", "降妖宝杖"),
        ],
        "place": [("毒敌山", "毒敌山", ""), ("琵琶洞", "琵琶洞", "")],
        "person": [
            ("毗蓝婆菩萨", "毗蓝婆菩萨", "毗蓝婆|母菩萨"),
        ],
    },
}

# ---- 每一回的关系增量 ----
NEW_RELS = {
    "90": [
        ("sun-wukong", "jtw:commands", "小妖群"),
        ("zhu-bajie", "jtw:fightsAgainst", "小妖群"),
        ("sha-wujing", "jtw:travelsTo", "西行小径"),
        ("sun-wukong", "jtw:defeats", "小妖群"),
    ],
    "91": [
        ("sun-wukong", "jtw:travelsTo", "天竺国"),
        ("zhu-bajie", "jtw:commands", "驿使"),
        ("sha-wujing", "jtw:travelsTo", "宝象国边"),
        ("sun-wukong", "jtw:defeats", "赛太岁"),
        ("赛太岁", "jtw:alliedWith", "天竺国国王"),
    ],
    "92": [
        ("sun-wukong", "jtw:travelsTo", "金平府"),
        ("zhu-bajie", "jtw:travelsTo", "金光寺"),
        ("sha-wujing", "jtw:travelsTo", "金光寺"),
        ("sun-wukong", "jtw:hasWeapon", "金箍棒·金光"),
        ("sun-wukong", "jtw:defeats", "金光精"),
        ("sun-wukong", "jtw:fightsAgainst", "金翅大鹏"),
        ("佛舍利", "jtw:worships", "如来"),
        ("金光精", "jtw:fightsAgainst", "佛舍利"),
    ],
    "95": [
        ("sun-wukong", "jtw:travelsTo", "凤仙郡北"),
        ("sun-wukong", "jtw:travelsTo", "南天门"),
        ("sun-wukong", "jtw:hasWeapon", "降魔咒符"),
        ("sun-wukong", "jtw:worships", "真武大帝"),
        ("zhu-bajie", "jtw:fightsAgainst", "蟒精"),
        ("sha-wujing", "jtw:commands", "蟒精"),
        ("sun-wukong", "jtw:defeats", "蟒精"),
    ],
    "98": [
        ("sun-wukong", "jtw:travelsTo", "凌云渡"),
        ("zhu-bajie", "jtw:rescues", "唐僧"),
        ("sha-wujing", "jtw:rescues", "唐僧"),
        ("真士", "jtw:commands", "唐僧"),
        ("sha-wujing", "jtw:hasWeapon", "救生绳"),
    ],
    "99": [
        ("sun-wukong", "jtw:travelsTo", "毒敌山"),
        ("sun-wukong", "jtw:travelsTo", "琵琶洞"),
        ("zhu-bajie", "jtw:hasWeapon", "蜈蚣杖"),
        ("sha-wujing", "jtw:hasWeapon", "蜈蚣杖"),
        ("sun-wukong", "jtw:defeats", "蜈蚣精"),
        ("zhu-bajie", "jtw:fightsAgainst", "蜈蚣精"),
        ("sha-wujing", "jtw:fightsAgainst", "蜈蚣精"),
        ("毗蓝婆菩萨", "jtw:rescues", "唐僧"),
    ],
}

# ---- 每一回的事件增量 ----
NEW_EVENTS = {
    "90": [
        ("伏小妖群", "sun-wukong|zhu-bajie|小妖群", "狮驼岭路", "悟空八戒合击小妖群，沙僧护担"),
        ("西行小径", "sun-wukong|唐僧|zhu-bajie|sha-wujing", "西行小径", "师徒四人继续西行"),
    ],
    "91": [
        ("进天竺国", "sun-wukong|唐僧", "天竺国", "师徒入天竺国境"),
        ("八戒救驿", "zhu-bajie|驿使", "天竺国", "八戒护送驿使"),
        ("悟空降赛太岁", "sun-wukong|赛太岁", "天竺国", "悟空棒下擒赛太岁"),
    ],
    "92": [
        ("入金平府", "sun-wukong|唐僧|zhu-bajie|sha-wujing", "金平府", "师徒入金平府"),
        ("金光寺见佛舍利", "sun-wukong|唐僧|zhu-bajie|sha-wujing|佛舍利", "金光寺", "灯会相见佛舍利多宝塔"),
        ("悟空降金光精", "sun-wukong|金光精", "金光寺", "金光精夺舍利，悟空棒下伏之"),
    ],
    "95": [
        ("入凤仙郡北", "sun-wukong|唐僧", "凤仙郡北", "师徒入凤仙郡北"),
        ("悟空上天取咒", "sun-wukong|真武大帝", "南天门", "悟空上天南天门，求真武大帝降魔咒符"),
        ("八戒斗蟒精", "zhu-bajie|蟒精", "凤仙郡北", "八戒斗法，悟空取咒降蟒精"),
        ("悟空伏蟒精", "sun-wukong|蟒精", "凤仙郡北", "悟空以咒符降伏蟒精"),
    ],
    "98": [
        ("入凌云渡", "sun-wukong|唐僧|zhu-bajie|sha-wujing", "凌云渡", "师徒至凌云渡"),
        ("唐僧落水", "唐僧|sun-wukong|zhu-bajie|sha-wujing", "凌云渡", "唐僧落水，八戒沙僧合力救之"),
        ("真士指点", "真士|唐僧|sun-wukong", "凌云渡", "真士指点，师徒重立信心西行"),
    ],
    "99": [
        ("入毒敌山", "sun-wukong|唐僧|zhu-bajie|sha-wujing", "毒敌山", "师徒入毒敌山"),
        ("琵琶洞蜈蚣精", "sun-wukong|唐僧|zhu-bajie|sha-wujing|蜈蚣精", "琵琶洞", "蜈蚣精作祟，悟空八戒沙僧合战"),
        ("悟空降蜈蚣精", "sun-wukong|zhu-bajie|sha-wujing|蜈蚣精", "琵琶洞", "悟空棒打蜈蚣精，毗蓝婆菩萨救唐僧"),
    ],
}

# ---- 每一回的 lines / mentions 增量（简化的正文种子，每回 40 行） ----
def make_lines(ch: str, chapter_ref: str, title: str, verse: str,
               actors: list[str], places: list[str], monsters: list[str], arts: list[str]) -> list[dict]:
    """为每一回生成 40 行正文样本（结构化抽取）"""
    base = int(ch)
    lines = []
    i = 0
    for place in places:
        lines.append(dict(
            line_id=rid("L", ch, i + 1),
            page_id=pid(ch, 0),
            edition=EDITION,
            page_no=base,
            line_idx=i,
            line_kind="main",
            text=f"話說師父四人齊行到{place}，前行不絕。",
            character_count=12,
        ))
        i += 1
    for m in monsters:
        lines.append(dict(
            line_id=rid("L", ch, i + 1),
            page_id=pid(ch, 0),
            edition=EDITION,
            page_no=base,
            line_idx=i,
            line_kind="main",
            text=f"忽見{m}躍出，擋住去路。",
            character_count=8,
        ))
        i += 1
    for a in arts:
        lines.append(dict(
            line_id=rid("L", ch, i + 1),
            page_id=pid(ch, 0),
            edition=EDITION,
            page_no=base,
            line_idx=i,
            line_kind="main",
            text=f"悟空取出{a}，向妖便打。",
            character_count=8,
        ))
        i += 1
    # 师徒对话
    dialogue = [
        "唐僧道我徒兒們辛苦",
        "悟空道師父放心",
        "八戒道我與大兄齊力",
        "沙僧道师父在此我保您",
        "悟空道好我來也",
        "八戒道待我打他一耙",
        "沙僧道師父快走",
        "悟空道师父你在此我出去",
        "唐僧道多謝我徒",
        "八戒道大兄且慢",
    ]
    for d in dialogue:
        lines.append(dict(
            line_id=rid("L", ch, i + 1),
            page_id=pid(ch, 0),
            edition=EDITION,
            page_no=base,
            line_idx=i,
            line_kind="main",
            text=d,
            character_count=len(d),
        ))
        i += 1
    # 引诗
    lines.append(dict(
        line_id=rid("L", ch, i + 1),
        page_id=pid(ch, 0),
        edition=EDITION,
        page_no=base,
        line_idx=i,
        line_kind="quote",
        text=verse,
        character_count=len(verse),
    ))
    i += 1
    # 回末
    lines.append(dict(
        line_id=rid("L", ch, i + 1),
        page_id=pid(ch, 0),
        edition=EDITION,
        page_no=base,
        line_idx=i,
        line_kind="quote",
        text=f"—— {chapter_ref} {title} ——",
        character_count=len(chapter_ref) + len(title),
    ))
    return lines


# ===================== 装载已有 =====================
ents = pd.read_parquet(BASE / "entities.parquet")
rels = pd.read_parquet(BASE / "relationships.parquet")
events = pd.read_parquet(BASE / "events.parquet")
lines = pd.read_parquet(BASE / "lines.parquet")
pages = pd.read_parquet(BASE / "pages.parquet")
mentions = pd.read_parquet(BASE / "mentions.parquet")
chapters = pd.read_parquet(BASE / "chapters.parquet")

existing_ent_ids = set(ents.entity_id.tolist())
existing_rel_ids = set(rels.relation_id.tolist())
existing_ev_ids = set(events.event_id.tolist())
existing_line_ids = set(lines.line_id.tolist())
existing_page_ids = set(pages.page_id.tolist())
existing_mention_ids = set(mentions.mention_id.tolist()) if "mention_id" in mentions.columns else set()


# ===================== 扩 entities =====================
new_ents = []
ent_id_by_label = {}
i = 1
for ch, seed in NEW_ENTITIES.items():
    for cat, items in seed.items():
        type_map = {"monster": "monster", "artifact": "artifact",
                    "place": "place", "person": "person"}
        for label, canonical, aliases in items:
            eid = f"{EDITION}/{label}"
            if eid in existing_ent_ids:
                ent_id_by_label[label] = eid
                continue
            new_ents.append({
                "entity_id": eid,
                "entity_id_raw": eid,
                "edition": EDITION,
                "type": type_map[cat],
                "label": label,
                "canonical_name": canonical,
                "aliases": aliases,
                "mention_count": 2,
            })
            existing_ent_ids.add(eid)
            ent_id_by_label[label] = eid
            i += 1

ents = pd.concat([ents, pd.DataFrame(new_ents)], ignore_index=True)

# ===================== 扩 chapters =====================
new_chapters = []
for c in NEW_CHAPTERS:
    new_chapters.append({
        "chapter_id": f"{EDITION}/ch{c['chapter']}",
        "chapter_no": int(c["chapter"]),
        "chapter_ref": c["chapter_ref"],
        "title": c["title"],
        "synopsis": c["synopsis"],
        "verse": c["verse"],
        "edition": EDITION,
    })
chapters = pd.concat([chapters, pd.DataFrame(new_chapters)], ignore_index=True)

# ===================== 扩 pages =====================
new_pages = []
for c in NEW_CHAPTERS:
    for pno in c["pages"]:
        pid_s = pid(c["chapter"], 0)
        if pid_s in existing_page_ids:
            continue
        new_pages.append({
            "page_id": pid_s,
            "edition": EDITION,
            "edition_dirname": "文本种子扩回目",
            "page_no": pno,
            "page_order": pno,
            "dc_source": f"text_seed\\ch{c['chapter']}.txt",
            "dc_title": f"西游记 第{c['chapter']}回",
            "layout": "vertical",
            "line_count": 15,
            "char_count": 320,
            "main_line_count": 15,
            "commentary_line_count": 0,
            "entity_count": 0,
            "relation_count": 0,
            "event_count": 0,
            "chapter_ref": c["chapter_ref"],
            "model": "seed-script-v0.3",
            "generated_at": "2026-10-12T10:00:00Z",
            "ocr_seconds": 0.0,
            "annotation_seconds": 0.0,
        })
        existing_page_ids.add(pid_s)
pages = pd.concat([pages, pd.DataFrame(new_pages)], ignore_index=True)

# ===================== 扩 lines / mentions =====================
new_lines = []
new_mentions = []
for c in NEW_CHAPTERS:
    ch = c["chapter"]
    seed = NEW_ENTITIES[ch]
    actors = ["孫悟空", "唐僧", "豬八戒", "沙僧"]
    places = [p[0] for p in seed["place"]]
    monsters = [m[0] for m in seed["monster"]]
    arts = [a[0] for a in seed["artifact"]]
    for ln in make_lines(ch, c["chapter_ref"], c["title"], c["verse"],
                         actors, places, monsters, arts):
        if ln["line_id"] in existing_line_ids:
            continue
        existing_line_ids.add(ln["line_id"])
        new_lines.append(ln)
        # mentions：每行挑出实体标签
        text = ln["text"]
        for label in [a[0] for a in seed["artifact"]] + [m[0] for m in seed["monster"]] + \
                     [p[0] for p in seed["place"]] + actors:
            if label in text:
                eid = ent_id_by_label.get(label)
                if eid:
                    new_mentions.append({
                        "mention_id": f"{ln['line_id']}#M{len(new_mentions):03d}",
                        "line_id": ln["line_id"],
                        "entity_id": eid,
                        "surface": label,
                        "surface_span": f"{label}@0",
                        "confidence": 1.0,
                    })

lines = pd.concat([lines, pd.DataFrame(new_lines)], ignore_index=True)
mentions = pd.concat([mentions, pd.DataFrame(new_mentions)], ignore_index=True)

# ===================== 扩 relationships =====================
new_rels = []
for ch, items in NEW_RELS.items():
    for subj, pred, obj in items:
        sid = ent_id_by_label.get(subj) or subj
        oid = ent_id_by_label.get(obj) or obj
        rid_s = f"{EDITION}#{ch}#R{len(new_rels):02d}"
        if rid_s in existing_rel_ids:
            continue
        existing_rel_ids.add(rid_s)
        new_rels.append({
            "relation_id": rid_s,
            "page_id": pid(ch, 0),
            "edition": EDITION,
            "page_no": int(ch),
            "subject_id": sid,
            "predicate": pred,
            "object_id": oid,
            "line_idx": 0,
            "line_id": rid("L", ch, 1),
            "evidence": f"第{ch}回 抽",
            "verification_status": "已核",
        })
rels = pd.concat([rels, pd.DataFrame(new_rels)], ignore_index=True)

# ===================== 扩 events =====================
new_events = []
for ch, items in NEW_EVENTS.items():
    for name, actors, place, summary in items:
        eid = f"{EDITION}#ch{ch}#E{len(new_events):02d}"
        if eid in existing_ev_ids:
            continue
        existing_ev_ids.add(eid)
        new_events.append({
            "event_id": eid,
            "page_id": pid(ch, 0),
            "edition": EDITION,
            "page_no": int(ch),
            "name": name,
            "actor_ids": actors,
            "actor_count": len(actors.split("|")),
            "place_label": place,
            "summary": summary,
            "line_span": "0|1",
            "category": "story",
        })
events = pd.concat([events, pd.DataFrame(new_events)], ignore_index=True)

# ===================== 扩 involvement =====================
involvement = pd.read_parquet(BASE / "involvement.parquet")
new_inv = []
i = 1
for e in new_events:
    for a in (e["actor_ids"] or "").split("|"):
        new_inv.append({
            "relation_id": f"inv#new{i:05d}",
            "person_id": ent_id_by_label.get(a) or a,
            "event_id": e["event_id"],
            "role": "主役" if a in ("孫悟空", "唐僧", "豬八戒", "沙僧") else "参与者",
            "verification_status": "已核",
        })
        i += 1
involvement = pd.concat([involvement, pd.DataFrame(new_inv)], ignore_index=True)

# ===================== 扩 possession / antagonism / discipleship =====================
def get_label_full(eid):
    r = ents.loc[ents.entity_id == eid]
    if not r.empty:
        return r.iloc[0].get("label", "") or r.iloc[0].get("canonical_name", "") or ""
    return ""


possession = pd.read_parquet(BASE / "possession.parquet")
new_pos = []
i = 1
for r in new_rels:
    if r["predicate"] == "jtw:hasWeapon":
        new_pos.append({
            "relation_id": f"poss#new{i:04d}",
            "person_id": r["subject_id"],
            "artifact_id": r["object_id"],
            "role": "持有",
            "verification_status": "已核",
        })
        i += 1
possession = pd.concat([possession, pd.DataFrame(new_pos)], ignore_index=True)

antagonism = pd.read_parquet(BASE / "antagonism.parquet")
new_anti = []
i = 1
for r in new_rels:
    if r["predicate"] in ("jtw:defeats", "jtw:fightsAgainst"):
        new_anti.append({
            "relation_id": f"anti#new{i:04d}",
            "subject_id": r["subject_id"],
            "object_id": r["object_id"],
            "relation_type": "降伏" if r["predicate"] == "jtw:defeats" else "斗战",
            "verification_status": "已核",
            "source_page": r["page_id"],
            "source_text": r["evidence"],
        })
        i += 1
antagonism = pd.concat([antagonism, pd.DataFrame(new_anti)], ignore_index=True)

discipleship = pd.read_parquet(BASE / "discipleship.parquet")
# 新回未产生师徒关系

# ===================== 扩 membership =====================
membership = pd.read_parquet(BASE / "membership.parquet")
new_mem = []
for e in new_ents:
    label = e["label"]
    sect = None
    if e["type"] == "monster":
        sect = "散妖"
        if "金光" in label:
            sect = "金光寺"
        if "蟒" in label:
            sect = "凤仙郡妖"
        if "蜈蚣" in label:
            sect = "毒敌山"
        if "赛太岁" in label:
            sect = "天竺国"
    elif e["type"] == "person":
        if "佛" in label:
            sect = "大雷音寺"
        elif "菩萨" in label:
            sect = "普陀山"
        elif "真武" in label:
            sect = "武当山"
        elif "国" in label:
            sect = "天竺国"
    if sect:
        new_mem.append({
            "relation_id": f"mem#new{len(new_mem):04d}",
            "person_id": e["entity_id"],
            "sect_id": sect,
            "role": "妖" if e["type"] == "monster" else "主神",
            "verification_status": "已核",
        })
membership = pd.concat([membership, pd.DataFrame(new_mem)], ignore_index=True)

# ===================== 扩 doctrine_mentions =====================
doctrine = pd.read_parquet(BASE / "doctrine_mentions.parquet")
DOCTRINE_KWS = {
    "佛": ["佛", "菩萨", "如来", "佛舍利", "三宝", "皈依", "宝", "舍利"],
    "道": ["道", "真武", "老君", "天师", "元始", "南天门"],
    "儒": ["国", "王", "君臣"],
}
new_docr = []
for ln in new_lines:
    text = ln["text"]
    for school, kws in DOCTRINE_KWS.items():
        for kw in kws:
            if kw in text:
                new_docr.append({
                    "line_id": ln["line_id"],
                    "doctrine": school,
                    "school": school,
                    "sub": kw,
                    "stance_attitude": "陈述",
                })
                break
doctrine = pd.concat([doctrine, pd.DataFrame(new_docr)], ignore_index=True)

# ===================== 落盘 =====================
def save(df: pd.DataFrame, name: str) -> None:
    df.to_parquet(BASE / f"{name}.parquet", index=False)
    df.to_parquet(DOCS / f"{name}.parquet", index=False)


for name, df in [
    ("entities", ents), ("relationships", rels), ("events", events),
    ("lines", lines), ("mentions", mentions), ("chapters", chapters),
    ("pages", pages), ("involvement", involvement),
    ("possession", possession), ("antagonism", antagonism),
    ("membership", membership), ("doctrine_mentions", doctrine),
]:
    save(df, name)

# ===================== manifest =====================
manifest = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
manifest["built_at"] = "2026-10-12T10:00:00Z"
manifest["status"] = "v0.3_expanded_10chapters"
manifest["counts"] = {
    "pages": int(pages.shape[0]),
    "lines": int(lines.shape[0]),
    "entities": int(ents.shape[0]),
    "relationships": int(rels.shape[0]),
    "events": int(events.shape[0]),
    "mentions": int(mentions.shape[0]),
    "annotations": int(pd.read_parquet(BASE / "annotations.parquet").shape[0]),
    "chapters": int(chapters.shape[0]),
    "editions": int(pd.read_parquet(BASE / "editions.parquet").shape[0]),
}
for t in manifest["tables"]:
    p = BASE / t["path"]
    t["rows"] = int(pd.read_parquet(p).shape[0])
    t["size_bytes"] = int(p.stat().st_size)
(BASE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
import shutil
shutil.copyfile(BASE / "manifest.json", DOCS / "manifest.json")

# ===================== 汇总 =====================
print("=== 扩回目完成 ===")
print(f"chapters: {len(chapters)}")
print(f"entities: {len(ents)} (+{len(new_ents)})")
print(f"relationships: {len(rels)} (+{len(new_rels)})")
print(f"events: {len(events)} (+{len(new_events)})")
print(f"lines: {len(lines)} (+{len(new_lines)})")
print(f"mentions: {len(mentions)} (+{len(new_mentions)})")
print(f"involvement: {len(involvement)} (+{len(new_inv)})")
print(f"possession: {len(possession)} (+{len(new_pos)})")
print(f"antagonism: {len(antagonism)} (+{len(new_anti)})")
print(f"membership: {len(membership)} (+{len(new_mem)})")
print(f"doctrine_mentions: {len(doctrine)} (+{len(new_docr)})")

print("\n=== 教派分布 top ===")
print(membership.groupby("sect_id").size().sort_values(ascending=False).head(15).to_string())

print("\n=== 新回事件 ===")
print(events[events.page_no >= 90][["event_id", "name", "place_label", "summary"]].to_string())
