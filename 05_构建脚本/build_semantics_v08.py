# -*- coding: utf-8 -*-
"""
构建 v0.8 语义层：把「现有已全量入图的多版本正文」补上本体 M/N/O/V/W/Z 层的实例数据。

现状（探查确认）：
  - 正文已全量：gubao 100 回 / baihui_xiangzhu 100 回 / zhu_ping(典藏简本) 66 回 /
    xinke_pingbi 实存批评本 4 回；editions 共 11 行。
  - doctrine_mentions、scholar_arguments 两张 W 层表为空。
  - lines 上无 register / voice / wit / motif 标注（隐性约束 M/N/O 层缺实例）。

本脚本产出：
  doctrine_mentions.parquet  —— 各版本 lines 的三教（儒/释/道）提及标注（W 层）
  scholar_arguments.parquet  —— 评点家学术论点入库（W 层）
  edition_tendency.parquet   —— 每版本 儒/释/道 三维倾向向量（Z 层）
  edition_lineage.parquet    —— 版本谱系边（V 层）
  line_semantics.parquet     —— lines 的 register/voice/wit/motif 标注（M/N/O 层）
  并同步写入 docs/data/，更新 manifest.json。

跑法：
  python 05_构建脚本/build_semantics_v08.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path("04_knowledge_data")
DOCS = Path("docs/data")
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ─────────────────────────────────────────────────────────────
# W 层 · 1. 学术评点（scholar_arguments）
# 依据《西游》批评史：张书绅/尤侗/刘廷玑/陈士奇/汪象旭/袁于令/鲁迅/胡适
# ─────────────────────────────────────────────────────────────
# 列：argument_id, scholar_id, work_title, school, argues_about, stance, evidence_line_id
SCHOLAR_ARGUMENTS = [
    # 张书绅《新说西游记》 —— 理学/纲常派，三教归儒
    dict(scholar_id="zhang-shushen", work_title="新说西游记", school="理学",
         argues_about="《西游》旨归", stance="三教归儒，西游实为阐发纲常伦理之书，非谈空谈玄",
         evidence_line_id=None),
    dict(scholar_id="zhang-shushen", work_title="新说西游记", school="理学",
         argues_about="悟空成佛", stance="心猿归正即修身养性、去欲存理之功，喻儒家克己复礼",
         evidence_line_id=None),
    # 尤侗《〈西游真诠〉序》 —— 佛学/华严
    dict(scholar_id="you-dong", work_title="西游真诠序", school="佛学",
         argues_about="《西游》义理", stance="殆《华严》之外篇也，以佛家因果轮回、心性解脱论西游",
         evidence_line_id=None),
    dict(scholar_id="you-dong", work_title="西游真诠序", school="佛学",
         argues_about="金蝉转世", stance="唐僧即金蝉子转世，取经乃佛门度化之旅，证佛法无边",
         evidence_line_id=None),
    # 刘廷玑《在园杂志》
    dict(scholar_id="liu-tingji", work_title="在园杂志", school="丹道",
         argues_about="《西游》性质", stance="证道之书，其中金丹炉鼎、阴阳五行之说隐于妖怪斗法之中",
         evidence_line_id=None),
    # 陈士奇《西游真诠》
    dict(scholar_id="chen-shiqi", work_title="西游真诠", school="丹道",
         argues_about="五众象征", stance="师徒五众配金木水火土五行，沿途妖魔鬼怪皆外魔内因之象",
         evidence_line_id=None),
    # 汪象旭《西游证道书》
    dict(scholar_id="wang-xiangxu", work_title="西游证道书", school="丹道",
         argues_about="车迟国斗法", stance="车迟三怪喻外丹符箓之妄，悟空破之彰内丹心性之正",
         evidence_line_id=None),
    # 袁于令（幔亭过客）《西游记题词》
    dict(scholar_id="yuan-yuling", work_title="西游记题词", school="文学",
         argues_about="《西游》文风", stance="以趣胜，嬉笑怒骂皆成文章，神魔游戏之中含讽世之旨",
         evidence_line_id=None),
    # 鲁迅《中国小说史略》
    dict(scholar_id="lu-xun", work_title="中国小说史略", school="考证",
         argues_about="《西游》源流", stance="世德堂本为现存最早刻本，神魔小说尤以明世德堂本为宗",
         evidence_line_id=None),
    dict(scholar_id="lu-xun", work_title="中国小说史略", school="考证",
         argues_about="故事性质", stance="游戏之作，虽极诞妄，然非作者别含深意，实为神魔小说集大成",
         evidence_line_id=None),
    # 胡适
    dict(scholar_id="hu-shi", work_title="西游记考证", school="考证",
         argues_about="作者与主旨", stance="嬉笑怒骂的滑稽小说，非道书非佛书，须作游戏文字读",
         evidence_line_id=None),
]


# ─────────────────────────────────────────────────────────────
# Z 层 · 2. 每版本三教倾向（edition_tendency）
# 儒/释/道 三维 0.0-1.0，属分析判断，标注 ver 供追溯
# ─────────────────────────────────────────────────────────────
EDITION_TENDENCY = [
    # (edition_id, 儒, 释, 道, 备注)
    ("shidetang",       0.30, 0.40, 0.55, "世德堂本（1592），儒释道合流而未偏锋"),
    ("li_ping",         0.35, 0.35, 0.50, "李卓吾评本，重人物与文趣，三教并观"),
    ("daqishi",         0.30, 0.35, 0.55, "大奇书本，承世德堂系统"),
    ("xinke_pingbi",    0.30, 0.45, 0.45, "新刻全像批评本，评点重文理与佛道源流"),
    ("zhenquan",        0.25, 0.55, 0.65, "陈士奇《西游真诠》，佛道并重偏丹道"),
    ("yangminzhai",     0.30, 0.40, 0.50, "杨闽斋本，坊刻简本，偏向世德堂"),
    ("minzhaitang",     0.30, 0.40, 0.50, "闽斋堂本，坊刻简本"),
    ("zhengdao",        0.25, 0.50, 0.70, "汪象旭《西游证道书》，丹道倾向最重"),
    ("gubao",           0.30, 0.40, 0.55, "世德堂系统古本（维基西游），近世德堂"),
    ("baihui_xiangzhu", 0.35, 0.50, 0.60, "悟元子百回详注，佛道并重略偏道"),
    ("zhu_ping",        0.40, 0.50, 0.35, "朱鼎臣《释厄传》典藏简本，佛儒较重、道淡"),
]


# ─────────────────────────────────────────────────────────────
# V 层 · 3. 版本谱系（edition_lineage）
# from -> to，附衍生态：直接重刻 / 删减加评 / 简本改写 / 评点增益
#  列：lineage_id, from_edition, to_edition, lineage_type, note
# ─────────────────────────────────────────────────────────────
EDITION_LINEAGE = [
    ("shidetang", "gubao",       "重刻",    "世德堂原文系统直承，维基《西游》古本"),
    ("shidetang", "daqishi",     "重刻",    "大奇书堂重刻世德堂本"),
    ("daqishi",   "yangminzhai", "简本",    "杨闽斋本依大奇书系统缩略"),
    ("yangminzhai","minzhaitang","重刻",    "闽斋堂承杨闽斋"),
    ("shidetang", "li_ping",     "加评",    "李卓吾评点本，正文近世德堂"),
    ("shidetang", "zhenquan",    "加评",    "陈士奇据世德堂系统作《真诠》"),
    ("zhenquan",  "zhengdao",    "加评",    "汪象旭《证道书》，丹道评点增益"),
    ("zhenquan",  "baihui_xiangzhu","加评", "悟元子百回详注，属真诠/证道评点系统"),
    ("shidetang", "zhu_ping",    "改写",    "朱鼎臣《释厄传》典藏简本，重写为十卷六六章"),
    ("shidetang", "xinke_pingbi","加评",    "新刻全像批评本，世德堂系统之清批评本"),
]


# ─────────────────────────────────────────────────────────────
# W 层 · 4. 三教提及标注（doctrine_mentions）——对既有 lines 做关键词匹配
# 列：line_id, doctrine, school, sub, stance_attitude
# ─────────────────────────────────────────────────────────────
DOCTRINE_KEYWORDS = {
    "释": [
        "佛", "菩萨", "如来", "观音", "文殊", "普贤", "弥勒", "伽蓝", "罗汉",
        "三宝", "皈依", "舍利", "金刚", "禅", "般若", "涅槃", "轮回", "因果",
        "善哉", "施主", "众生", "禅定", "悟空", "金蝉", "灵山", "阿难", "迦叶",
        "须菩提", "紧箍", "经文", "经卷", "斋戒", "剃度", "比丘", "优婆塞",
    ],
    "道": [
        "道", "老君", "太上", "天尊", "元始", "灵宝", "真武", "南极", "天师",
        "三清", "四御", "金丹", "丹道", "内丹", "炉鼎", "符箓", "咒", "法印",
        "方术", "真人", "洞府", "仙山", "元君", "北斗", "南斗", "紫微", "雷部",
        "阎君", "幽冥", "地府", "奈何", "轮回", "阳寿", "长生", "金丹大道", "玄门",
        "天仙", "地仙", "飞升", "蟠桃", "仙丹", "八卦炉",
    ],
    "儒": [
        "君", "臣", "父", "子", "忠", "孝", "仁", "义", "礼", "智", "信",
        "纲", "常", "伦", "王", "国", "朝", "殿", "御", "圣旨", "丹墀", "金銮",
        "科举", "官", "吏", "民", "天下", "社稷", "礼部", "翰林", "丞相", "将军",
        "忠臣", "孝子", "贤君", "王道",
    ],
}


def build_doctrine_mentions(lines: pd.DataFrame) -> pd.DataFrame:
    rows = []
    text = lines["text"].astype(str).tolist()
    line_ids = lines["line_id"].tolist()
    for lid, t in zip(line_ids, text):
        hit = set()
        for sch, kws in DOCTRINE_KEYWORDS.items():
            if any(kw in t for kw in kws):
                hit.add(sch)
        for sch in hit:
            sub = None
            for kw in DOCTRINE_KEYWORDS[sch]:
                if kw in t:
                    sub = kw
                    break
            rows.append(dict(
                line_id=lid,
                doctrine=sch,
                school=sch,
                sub=sub,
                stance_attitude="陈述",
            ))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# M/N/O 层 · 5. 隐性约束实例（line_semantics）
# 列：line_id, edition, page_no, register_id, voice_id, wit_type, humor_level, motif_id
# 用 sub 串匹配，近似给分，供语义分析页展示，非严格标注
# ─────────────────────────────────────────────────────────────
REGISTER_TOKENS = {
    "market_colloquial": ["話說", "却说", "原来", "正是", "只见", "那", "来", "咱", "你", "我", "得", "啥"],
    "buddhist_chant":    ["佛", "菩萨", "如来", "三藏", "经文", "善哉", "阿弥陀", "因果", "皈依", "金蝉"],
    "daoist_chant":      ["太上", "天尊", "大道", "三清", "灵宝", "金丹", "老君", "真武", "玄门", "道"],
    "poetry_song":       ["詩曰", "词曰", "赋曰", "有诗为证", "诗曰", "正是", "但见那"],
    "monster_battle":    ["妖", "怪", "精", "泼", "棒", "打", "定住", "现出", "现原形", "斗", "战"],
    "monkey_mischief":   ["哈哈", "嘻嘻", "耍", "顽", "捉弄", "闹", "撒泼", "猢狲", "老孙"],
    "monarch_speech":    ["朕", "寡人", "王", "天朝", "朝廷", "敕", "圣旨", "御", "驾"],
    "narrator_voice":    ["話說", "却说", "且说", "只见", "忽见", "再说", "单表", "却说那"],
    "demon_speech":      ["小猢狲", "和尚", "吃", "剥皮", "蒸", "师父", "老孙", "妖精"],
}

VOICE_TOKENS = {
    "wukong_scholar":      ["灵长", "学道", "妙理", "大圣"],
    "wukong_monkey":       ["老孙", "泼猴", "俺老孙", "爷爷在此"],
    "wukong_mischievous":  ["呆子", "八戒", "耍子", "弄个", "顽皮"],
    "tang_sutra":          ["阿弥陀佛", "贫僧", "善哉", "经文", "三藏", "悟空休", "徒弟"],
    "tang_melancholy":     ["泪", "伤", "悲", "思乡", "徒弟何在"],
    "zhujie_glutton":      ["八戒", "饿", "吃", "耙", "偷懒", "睡了"],
    "shajiej_steady":      ["沙", "莫吵", "大师兄", "担", "稳"],
    "yaojing_provoke":     ["妖精", "变", "大王", "吃你", "蒸你"],
}

WIT_TOKENS = {
    "戏谑": ["哈哈", "笑道", "耍子", "顽"],
    "反讽": ["真好", "妙极", "承情", "多谢"],
    "谐音": ["原作", "（原", "似另有"],
    "胡闹": ["翻筋斗", "捉弄", "闹", "顽耍"],
    "挑衅": ["你且", "来者", "吃我一棒", "老孙来也"],
    "自嘲": ["老猪", "俺老孙", "小圣"],
    "冷幽默": ["不意", "倒是", "却原来"],
    "双关": ["金箍", "紧箍", "妙"],
}


def classify_by_tokens(text: str, table: dict) -> list[str]:
    hits = []
    for name, toks in table.items():
        if any(t in text for t in toks):
            hits.append(name)
    return hits


def build_line_semantics(lines: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in lines.iterrows():
        t = str(r.get("text", ""))
        regs = classify_by_tokens(t, REGISTER_TOKENS)
        register_id = regs[0] if regs else "narrator_voice"
        voices = classify_by_tokens(t, VOICE_TOKENS)
        voice_id = voices[0] if voices else None
        wits = classify_by_tokens(t, WIT_TOKENS)
        wit_type = wits[0] if wits else None
        humor_level = round(min(len(wits) / 3, 1.0), 2) if wits else 0.0
        rows.append(dict(
            line_id=r["line_id"],
            edition=r.get("edition"),
            page_no=r.get("page_no"),
            register_id=register_id,
            voice_id=voice_id,
            wit_type=wit_type,
            humor_level=humor_level,
            motif_id="monster_subdue" if wit_type and any(k in t for k in ["妖", "怪", "斗", "棒"]) else None,
        ))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# 落盘
# ─────────────────────────────────────────────────────────────
def write(df: pd.DataFrame, name: str) -> pd.DataFrame:
    if df is not None and not df.empty:
        df.to_parquet(BASE / f"{name}.parquet", index=False)
        df.to_parquet(DOCS / f"{name}.parquet", index=False)
    else:
        print(f"  [skip] {name}: 0 rows")
    return df


def update_manifest():
    m = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
    m["built_at"] = NOW
    m["status"] = "v0.8_semantics_layers"
    # 重建 counts / tables 反映真实 parquet
    names = ["annotations", "antagonism", "artifacts", "chapters", "discipleship",
             "doctrine_mentions", "edition_lineage", "edition_tendency", "editions",
             "entities", "events", "involvement", "kinship", "line_semantics",
             "lines", "membership", "mentions", "pages", "possession",
             "relationships", "scholar_arguments", "stats"]
    tables = []
    counts = {}
    for n in names:
        p = BASE / f"{n}.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            tables.append({"name": n, "path": f"{n}.parquet",
                           "rows": len(df), "size_bytes": int(p.stat().st_size)})
            counts[n] = len(df)
    m["counts"] = counts
    m["tables"] = tables
    (BASE / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    import shutil
    shutil.copyfile(BASE / "manifest.json", DOCS / "manifest.json")
    return counts


def main() -> int:
    lines = pd.read_parquet(BASE / "lines.parquet")
    print(f"lines 总数: {len(lines)}")

    # W 层 scholar_arguments
    sa = pd.DataFrame(SCHOLAR_ARGUMENTS)
    sa.insert(0, "argument_id", [f"sch-arg-{i:03d}" for i in range(len(sa))])
    write(sa, "scholar_arguments")

    # W 层 doctrine_mentions（重建）
    dm = build_doctrine_mentions(lines)
    print(f"doctrine_mentions: {len(dm)}  (儒释道分布): "
          f"{dm['doctrine'].value_counts().to_dict() if not dm.empty else {}}")
    write(dm, "doctrine_mentions")

    # Z 层 edition_tendency
    et = pd.DataFrame(EDITION_TENDENCY, columns=["edition_id", "confucian", "buddhist", "daoist", "note"])
    et.insert(0, "tendency_id", [f"tend-{i:03d}" for i in range(len(et))])
    write(et, "edition_tendency")

    # V 层 edition_lineage
    el = pd.DataFrame(EDITION_LINEAGE, columns=["from_edition", "to_edition", "lineage_type", "note"])
    el.insert(0, "lineage_id", [f"lineage-{i:03d}" for i in range(len(el))])
    write(el, "edition_lineage")

    # M/N/O 层 line_semantics
    ls = build_line_semantics(lines)
    print(f"line_semantics: {len(ls)}  (register 分布): "
          f"{ls['register_id'].value_counts().head(8).to_dict()}")
    write(ls, "line_semantics")

    # 更新 manifest
    counts = update_manifest()
    print("\n=== manifest 更新完成 ===")
    for k in ["pages", "lines", "chapters", "editions", "entities", "relationships",
              "events", "mentions", "annotations", "doctrine_mentions",
              "scholar_arguments", "edition_tendency", "edition_lineage", "line_semantics"]:
        print(f"  {k:20s}: {counts.get(k, 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
