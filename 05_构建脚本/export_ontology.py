# -*- coding: utf-8 -*-
"""导出本体四层数据到 docs/data/ontology.json，供 docs/query.html 检索展示。

四层：
  form      形态层 — Page / TextLine / Annotation（版式与文本形态）
  thematic  主题层 — Entity / Relationship / Event / Artifact（人物/事件/关系）
  ideological 思想层 — ScholarArgument / DoctrineMention（评点家观点、义理）
  textual   版本层 — Edition / Chapter / Line（版本谱系与章回）

读入：
  03_本体论规范/jtw_kg_ontology.ttl    本体类与属性定义
  03_本体论规范/vocabularies.yaml     受控词表
  04_knowledge_data/*.parquet         数据表

输出：
  docs/data/ontology.json             四层结构 + 类统计 + 样例记录

跑法：
  py -3 05_构建脚本/export_ontology.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
ONTOL = ROOT / "03_本体论规范"
DATA = ROOT / "04_knowledge_data"
OUT_DIR = ROOT / "docs" / "data"
OUT = OUT_DIR / "ontology.json"

# ──────────────────────────────────────────────
# 1. 解析 TTL —— 提取类和属性定义
# ──────────────────────────────────────────────
CLASS_RE = re.compile(r"^jtw:(\w+)\s+(?:rdfs:label|a owl:(?:Class|DatatypeProperty|ObjectProperty))")
CLASS_BLOCK_RE = re.compile(
    r"^jtw:(\w+)\s*$|jtw:(\w+)\s+(?=[a-zA-Z:])", re.M
)


def parse_ttl(path: Path) -> dict:
    """解析 TTL：按 '.' 结束一条 triple-block（多行以 ';' 串联）。

    只关心 jtw: 开头的类和属性，抽取 label_zh / comment_zh / domain / range / subClassOf。
    """
    text = path.read_text(encoding="utf-8")
    # 去掉 # 注释行
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("@prefix"):
            continue
        lines.append(s)
    text = "\n".join(lines)

    # 把多行 ';'-连接压成一行，再用 '.' 切分完整声明
    text_flat = re.sub(r";\s*\n\s*", " ; ", text)
    blocks = [b.strip() for b in text_flat.split(".") if b.strip()]
    classes = {}
    properties = {}
    for stmt in blocks:
        m = re.match(r"(?:jtw:(\w+)|<[^>]+jtw-kg#(\w+)>)", stmt)
        if not m:
            continue
        subj = m.group(1) or m.group(2)
        block = {"name": subj}
        m2 = re.search(r'rdfs:label\s+"([^"]+)"@zh', stmt)
        if m2:
            block["label_zh"] = m2.group(1)
        m2 = re.search(r'rdfs:comment\s+"([^"]+)"@zh', stmt)
        if m2:
            block["comment_zh"] = m2.group(1)
        m2 = re.search(r'rdfs:domain\s+jtw:(\w+)', stmt)
        if m2:
            block["domain"] = m2.group(1)
        m2 = re.search(r'rdfs:range\s+(?:jtw:(\w+)|xsd:(\w+))', stmt)
        if m2:
            block["range"] = m2.group(1) or m2.group(2)
        m2 = re.search(r'rdfs:subClassOf\s+([\w:/#]+(?:\s*,\s*[\w:/#]+)*)', stmt)
        if m2:
            block["subClassOf"] = [s.strip().split("#")[-1].split("/")[-1]
                                   for s in m2.group(1).split(",")]
        # 分类：Class vs Property
        is_property = "rdfs:domain" in stmt and "rdfs:range" in stmt
        # 提取主语言（首词）
        m3 = re.match(r"(\w+)(?::\w+)?", stmt)
        first = m3.group(1) if m3 else ""
        block["_kind"] = "property" if is_property else "class"
        block["_first_token"] = first
        if is_property:
            properties[subj] = block
        else:
            classes[subj] = block
    return {"classes": classes, "properties": properties}


# ──────────────────────────────────────────────
# 2. 词表
# ──────────────────────────────────────────────
def load_vocab(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ──────────────────────────────────────────────
# 3. 数据表统计 + 样例
# ──────────────────────────────────────────────
LAYER_TABLES = {
    "form": ["pages", "lines", "annotations", "line_semantics"],
    "thematic": ["entities", "relationships", "events", "artifacts",
                 "discipleship", "kinship", "antagonism", "possession",
                 "membership", "involvement", "mentions"],
    "ideological": ["scholar_arguments", "doctrine_mentions"],
    "textual": ["editions", "chapters", "edition_tendency", "edition_lineage"],
}

TABLE_DESC = {
    "pages": "页面（含 OCR 与形态统计）",
    "lines": "文本段（形态层，form_type 区分正文/评点/诗词）",
    "annotations": "评点行（眉批/夹批/旁批/回前/回后/图注/题署/序跋）",
    "line_semantics": "文本行语义标注（register/voice/wit/motif 四维隐性约束实例）",
    "entities": "实体（人物/妖魔/法宝/地点/官职/引文/宗教）",
    "relationships": "关系（subject→predicate→object，含证据与核实状态）",
    "events": "事件（含主演、地点、摘要、事件类别）",
    "artifacts": "法宝（持有者/来源/状态）",
    "discipleship": "师徒关系（含是否正式、证据）",
    "kinship": "亲属关系",
    "antagonism": "敌对关系",
    "possession": "法宝持有",
    "membership": "派系归属",
    "involvement": "事件参与角色",
    "mentions": "实体×文本行 提及",
    "scholar_arguments": "评点家观点（含学派、立场）",
    "doctrine_mentions": "义理提及（佛/道/儒）",
    "editions": "版本名录（源流/年份/刊刻机构）",
    "chapters": "章回（回号/回目/所属版本）",
    "edition_tendency": "版本三教倾向（儒/释/道三维评分，Z 层）",
    "edition_lineage": "版本谱系（派生关系与衍生态，V 层）",
}


def load_table(name: str):
    p = DATA / f"{name}.parquet"
    if not p.exists():
        return None, []
    df = pd.read_parquet(p)
    return df, list(df.columns)


def df_samples(df: pd.DataFrame, cols: list, n: int = 5) -> list:
    if df is None or df.empty:
        return []
    sub = df[cols].head(n)
    rows = []
    for _, r in sub.iterrows():
        row = {}
        for c, v in r.items():
            if pd.isna(v):
                row[c] = None
            elif isinstance(v, (list, tuple, set)):
                row[c] = list(v)
            else:
                row[c] = str(v) if len(str(v)) > 500 else v
        rows.append(row)
    return rows


def df_stats(df: pd.DataFrame) -> dict:
    """关键分组的计数。"""
    stats = {"rows": int(len(df))}
    if df is None or df.empty:
        return stats
    for col in ("edition", "type", "form_type", "predicate", "category",
                "relation_type", "role", "school", "stance", "doctrine",
                "verification_status"):
        if col in df.columns:
            vc = df[col].dropna().astype(str).value_counts()
            stats[col] = {str(k): int(v) for k, v in vc.head(20).items()}
    return stats


def build_layer(layer_name: str, table_names: list) -> dict:
    layer = {"tables": {}, "totals": {}}
    total_rows = 0
    for name in table_names:
        df, cols = load_table(name)
        info = {
            "name": name,
            "desc": TABLE_DESC.get(name, ""),
            "columns": cols,
            "stats": df_stats(df),
            "samples": df_samples(df, cols, n=4),
        }
        layer["tables"][name] = info
        total_rows += len(df) if df is not None else 0
    layer["totals"]["rows"] = total_rows
    return layer


# ──────────────────────────────────────────────
# 4. 主流程
# ──────────────────────────────────────────────
def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    ttl = parse_ttl(ONTOL / "jtw_kg_ontology.ttl")
    vocab = load_vocab(ONTOL / "vocabularies.yaml")

    layers = {}
    for lname, tnames in LAYER_TABLES.items():
        layers[lname] = build_layer(lname, tnames)

    out = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "project": "西游记多版本古籍知识图谱本体",
            "layers": [
                {"id": "form", "label": "形态层", "en": "Formal",
                 "desc": "页面、段落、字符 — OCR 与版式证据链"},
                {"id": "thematic", "label": "主题层", "en": "Thematic",
                 "desc": "人物、事件、法宝、关系 — 剧情子图一等实体"},
                {"id": "ideological", "label": "思想层", "en": "Ideological",
                 "desc": "评点家观点、义理提及 — 佛道儒三教与批评学"},
                {"id": "textual", "label": "版本层", "en": "Textual",
                 "desc": "版本、章回、文本行 — 版本谱系与章回结构"},
            ],
        },
        "ontology": ttl,
        "vocabularies": vocab,
        "layers": layers,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"已写入 {OUT.relative_to(ROOT)}  ({size_kb:.1f} KB)")

    print("\n各层数据行合计：")
    for lname, linfo in layers.items():
        print(f"  {lname:12s} rows={linfo['totals']['rows']:>6d}")
        for tname, tinfo in linfo["tables"].items():
            r = tinfo["stats"].get("rows", 0)
            print(f"    - {tname:22s} {r:>6d}")

    print(f"\n本体类 {len(ttl['classes'])} / 属性 {len(ttl['properties'])}")
    print(f"词表键 {len(vocab)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
