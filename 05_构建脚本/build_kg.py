#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""西游记 KG 数据层构建器 — Parquet + manifest.json

输入：book/extract/{edition}/pNNNNN.jsonld
     每个 JSON-LD 页面对应一个 jtw:BookPage，含：
       - jtw:editionCode / jtw:pageNo / dc:source / prov:usedTool
       - jtw:ocr.lines（形态层，每条含 type/text/conf）
       - jtw:stats（页级统计）
       - jtw:entities（人物/事件/地点，一等实体）
       - jtw:relationships（关系一等实体）
       - jtw:events（事件一等实体）
       - jtw:timings（抽取用时）

输出：04_knowledge_data/*.parquet + manifest.json
  pages.parquet         页面层
  lines.parquet         文本段层（形态层）
  editions.parquet      版本名录（含 16 版本源流信息）
  chapters.parquet      章回层（从 OCR 提取的 title 行推断）
  entities.parquet      实体一等实体（人物/妖魔/法宝/地点...）
  relationships.parquet 关系一等实体
  events.parquet        事件一等实体
  mentions.parquet      实体×文本行 提及关系
  annotations.parquet   评点行（form_type ∈ pre/post/inline/top/side/bottom/caption/colophon/preface）
  stats.parquet         页级统计聚合
  manifest.json         清单 + schema + 表统计

用法：
  python build_kg.py            # 从 book/extract/**.jsonld 扫描并写入 Parquet
  python build_kg.py --dry      # 只扫描不写
"""
import os
import sys
import re
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    print("缺少依赖：pip install pandas pyarrow")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "04_knowledge_data"
LOG_DIR = ROOT / "05_构建脚本" / "logs"
EXTRACT_DIR = ROOT / "book" / "extract"

# 形态类型：区分评点 vs 正文
COMMENTARY_FORMS = {"pre", "post", "inline", "top", "side", "bottom", "caption", "colophon", "preface"}

# 章回标题正则：第XX回 / 第XX卷 / 卷XX
CHAPTER_RE = re.compile(r"第[〇零一二三四五六七八九十百千万0-9○零○一二三四五六七八九十百]+[回卷]")


def log(msg: str):
    ts = time.strftime("[%H:%M:%S]")
    print(f"{ts} {msg}")


def ensure_out():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# 版本信息表（16 版源流，来自 vocabularies.yaml 的 edition_id）
# ──────────────────────────────────────────────
EDITIONS_SEED = [
    ("shidetang", "世德堂本", 1592, "金陵世德堂", "现存最早刻本，1592"),
    ("li_ping", "李评本", None, "明李廷机评点本", "含评点"),
    ("daqishi", "大奇书本", None, "大奇书堂", "Gallica 分册 4031-4035"),
    ("xinke_pingbi", "新刻全像批评西游记", None, "清", "含评点"),
    ("zhenquan", "真诠本", None, "清陈士奇", "含评点"),
    ("yangminzhai", "杨闽斋本", None, "杨闽斋堂", ""),
    ("minzhaitang", "闽斋堂本", None, "闽斋堂", ""),
    ("zhengdao", "证道本", None, "清证道本", ""),
]


# ──────────────────────────────────────────────
# 扫描：遍历 book/extract/{edition}/*.jsonld
# ──────────────────────────────────────────────
def scan_extract_dir() -> Dict[str, List[Dict[str, Any]]]:
    result = {
        "pages": [],
        "lines": [],
        "entities": [],
        "relationships": [],
        "events": [],
        "mentions": [],
        "annotations": [],
        "chapters_raw": [],
        "stats": [],
    }
    for edition_dir in EXTRACT_DIR.iterdir():
        if not edition_dir.is_dir():
            continue
        if edition_dir.name.startswith("_") or edition_dir.name == "pdf-ocr-raw":
            continue
        edition_dirname = edition_dir.name  # 中文目录名
        jsonld_files = sorted(edition_dir.glob("p*.jsonld"))
        for jf in jsonld_files:
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
            except Exception as e:
                log(f"[warn] 无法解析 {jf.name}: {e}")
                continue

            # 关键字段（对齐真实 JSON-LD schema）
            edition_code = data.get("jtw:editionCode") or edition_dirname
            page_no = data.get("jtw:pageNo") or data.get("jtw:pageOrderInEdition")
            if page_no is None:
                m = re.match(r"p(\d+)", jf.stem)
                page_no = int(m.group(1)) if m else 0
            page_no = int(page_no)
            page_id = f"{edition_code}#p{page_no:05d}"

            image_path = data.get("dc:source", "")
            title = data.get("dc:title", "")
            ocr = data.get("jtw:ocr", {}) or {}
            layout = ocr.get("layout", "")
            raw_lines = ocr.get("lines", []) or []
            page_meta = ocr.get("page_meta", {}) or {}
            annotation = data.get("jtw:annotation", {}) or {}
            stats = data.get("jtw:stats", {}) or {}
            timings = data.get("jtw:timings", {}) or {}
            model = data.get("prov:usedTool", "")
            generated_at = data.get("prov:wasGeneratedAt", "")

            # 1. page 行
            result["pages"].append({
                "page_id": page_id,
                "edition": edition_code,
                "edition_dirname": edition_dirname,
                "page_no": page_no,
                "page_order": data.get("jtw:pageOrderInEdition", page_no),
                "dc_source": image_path,
                "dc_title": title,
                "layout": layout,
                "line_count": stats.get("line_count", len(raw_lines)),
                "char_count": sum(len(l.get("text", "")) for l in raw_lines),
                "main_line_count": stats.get("main_line_count", 0),
                "commentary_line_count": stats.get("commentary_line_count", 0),
                "entity_count": stats.get("entity_count", 0),
                "relation_count": stats.get("relation_count", 0),
                "event_count": stats.get("event_count", 0),
                "chapter_ref": stats.get("chapter_ref", annotation.get("chapter_ref", "")),
                "model": model,
                "generated_at": generated_at,
                "ocr_seconds": timings.get("ocr_seconds", 0),
                "annotation_seconds": timings.get("annotation_seconds", 0),
            })

            # 2. lines 行 + 3. mentions 行 + 4. annotations 行
            # 先建立 line_idx → line_id 的映射（供 mentions 引用）
            line_id_map = {}
            entities_list = data.get("jtw:entities", []) or []
            for i, ln in enumerate(raw_lines):
                line_id = f"{page_id}#L{i:03d}"
                line_id_map[i] = line_id
                form_type = ln.get("type", "main")
                text = ln.get("text", "")
                conf = float(ln.get("conf", 0.0))
                result["lines"].append({
                    "line_id": line_id,
                    "page_id": page_id,
                    "edition": edition_code,
                    "page_no": page_no,
                    "line_idx": i,
                    "form_type": form_type,
                    "text": text,
                    "char_count": len(text),
                    "confidence": conf,
                    "is_commentary": form_type in COMMENTARY_FORMS,
                })

            # 章回识别：line 里含"第XX回"字样
            for i, ln in enumerate(raw_lines):
                if ln.get("type") == "title":
                    text = ln.get("text", "")
                    if CHAPTER_RE.search(text):
                        result["chapters_raw"].append({
                            "edition": edition_code,
                            "page_no": page_no,
                            "line_id": line_id_map.get(i, f"{page_id}#L{i:03d}"),
                            "raw_title": text,
                        })

            # 5. entities（一等实体）
            for ent in entities_list:
                ent_id_raw = ent.get("id", "")
                ent_id = f"{edition_code}/{ent_id_raw}" if ent_id_raw else ""
                mentions_list = ent.get("mentions", []) or []
                aliases = ent.get("aliases", []) or []
                result["entities"].append({
                    "entity_id": ent_id,
                    "entity_id_raw": ent_id_raw,
                    "edition": edition_code,
                    "type": ent.get("type", ""),
                    "label": ent.get("label", ""),
                    "canonical_name": ent.get("canonical_name", ""),
                    "aliases": "|".join(aliases),
                    "mention_count": len(mentions_list),
                })
                # 6. mentions
                for m in mentions_list:
                    li = m.get("line_idx")
                    if li is not None:
                        result["mentions"].append({
                            "entity_id": ent_id,
                            "entity_id_raw": ent_id_raw,
                            "entity_type": ent.get("type", ""),
                            "line_id": line_id_map.get(int(li), f"{page_id}#L{int(li):03d}"),
                            "mention_text": m.get("text", ""),
                        })

            # 7. relationships
            for r in data.get("jtw:relationships", []) or []:
                result["relationships"].append({
                    "relation_id": f"{page_id}#R{len(result['relationships'])}",
                    "page_id": page_id,
                    "edition": edition_code,
                    "page_no": page_no,
                    "subject_id": r.get("subject_id", ""),
                    "predicate": r.get("predicate", ""),
                    "object_id": r.get("object", r.get("object_id", "")),
                    "line_idx": r.get("line_idx"),
                    "line_id": line_id_map.get(r.get("line_idx"), "") if r.get("line_idx") is not None else "",
                    "evidence": r.get("evidence", ""),
                    "verification_status": "待核实",  # 初稿，未交叉验证
                })

            # 8. events
            for ev in data.get("jtw:events", []) or []:
                lines_span = ev.get("lines", []) or []
                result["events"].append({
                    "event_id": f"{page_id}#E{len(result['events'])}",
                    "page_id": page_id,
                    "edition": edition_code,
                    "page_no": page_no,
                    "name": ev.get("name", ""),
                    "actor_ids": "|".join(ev.get("actor_ids", []) or []),
                    "actor_count": len(ev.get("actor_ids", []) or []),
                    "place_label": ev.get("place_label", ""),
                    "summary": ev.get("summary", ""),
                    "line_span": "|".join(str(x) for x in lines_span),
                    "category": "",  # 待人工/二次抽取补
                })

            # 9. annotations（评点行）
            for i, ln in enumerate(raw_lines):
                form = ln.get("type", "main")
                if form in COMMENTARY_FORMS:
                    result["annotations"].append({
                        "annotation_id": line_id_map[i],
                        "page_id": page_id,
                        "edition": edition_code,
                        "page_no": page_no,
                        "line_idx": i,
                        "form_type": form,
                        "text": ln.get("text", ""),
                        "confidence": float(ln.get("conf", 0.0)),
                        "chapter_ref": stats.get("chapter_ref", ""),
                    })

            # 10. stats 行（页级）
            result["stats"].append({
                "page_id": page_id,
                "edition": edition_code,
                "page_no": page_no,
                "line_count": stats.get("line_count", 0),
                "commentary_line_count": stats.get("commentary_line_count", 0),
                "main_line_count": stats.get("main_line_count", 0),
                "title_line_count": stats.get("title_line_count", 0),
                "entity_count": stats.get("entity_count", 0),
                "relation_count": stats.get("relation_count", 0),
                "event_count": stats.get("event_count", 0),
                "chapter_ref": stats.get("chapter_ref", ""),
            })

    return result


# ──────────────────────────────────────────────
# 章回层（从 raw 聚合）
# ──────────────────────────────────────────────
def normalize_chapter(raw_title: str) -> Tuple[str, str]:
    """从"第八十六回 水母助威征怪物 金公施法滅妖邪"提取 (chapter_no_str, chapter_title)"""
    m = CHAPTER_RE.search(raw_title)
    if not m:
        return "", raw_title
    prefix = m.group(0)  # 第XX回
    title_rest = raw_title[m.end():].strip()
    return prefix, title_rest


# ──────────────────────────────────────────────
# 写入 Parquet
# ──────────────────────────────────────────────
def write_table(name: str, rows: List[Dict[str, Any]], cols=None):
    if not rows:
        if cols:
            df = pd.DataFrame({c: [] for c in cols})
        else:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame(rows)
    pq.write_table(pa.Table.from_pandas(df), OUT_DIR / f"{name}.parquet")
    log(f"[write] {name}.parquet  rows={len(df)}")


def write_editions():
    rows = []
    for eid, disp, year, pub, desc in EDITIONS_SEED:
        rows.append({
            "edition_id": eid,
            "display_name": disp,
            "year": year if year is not None else -1,
            "publisher": pub,
            "desc": desc,
        })
    write_table("editions", rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    ensure_out()
    log(f"[scan] {EXTRACT_DIR}")
    data = scan_extract_dir()
    log(f"[scan] pages={len(data['pages'])} lines={len(data['lines'])} "
        f"entities={len(data['entities'])} rels={len(data['relationships'])} "
        f"events={len(data['events'])} mentions={len(data['mentions'])} "
        f"annos={len(data['annotations'])} chapters_raw={len(data['chapters_raw'])}")

    if args.dry:
        log("[dry] 不写文件")
        return

    # editions 种子表
    write_editions()

    # 主表：pages / lines / entities / relationships / events / mentions / annotations / stats
    for name in ("pages", "lines", "entities", "relationships", "events",
                 "mentions", "annotations", "stats"):
        write_table(name, data[name])

    # chapters：从 chapters_raw 聚合
    chapters = []
    seen = set()
    for row in data["chapters_raw"]:
        prefix, title = normalize_chapter(row["raw_title"])
        key = (row["edition"], prefix)
        if key in seen:
            continue
        seen.add(key)
        chapters.append({
            "chapter_id": f"{row['edition']}/{prefix}",
            "edition": row["edition"],
            "chapter_label": prefix,
            "chapter_title": title,
            "raw_title": row["raw_title"],
            "first_page": row["page_no"],
            "first_line_id": row["line_id"],
        })
    write_table("chapters", chapters)

    # 空表骨架：为后续 Agent 填充预留
    for name, cols in {
        "artifacts": ["artifact_id", "name", "origin", "state", "holder_id"],
        "discipleship": ["relation_id", "master_id", "disciple_id", "relation_type", "is_official", "verification_status", "source_page", "source_text"],
        "kinship": ["relation_id", "subject_id", "object_id", "relation_type", "verification_status", "source_page", "source_text"],
        "antagonism": ["relation_id", "subject_id", "object_id", "relation_type", "verification_status", "source_page", "source_text"],
        "membership": ["relation_id", "person_id", "sect_id", "role", "verification_status"],
        "possession": ["relation_id", "person_id", "artifact_id", "role", "verification_status"],
        "involvement": ["relation_id", "person_id", "event_id", "role", "verification_status"],
        "doctrine_mentions": ["line_id", "doctrine", "school", "sub", "stance_attitude"],
        "scholar_arguments": ["argument_id", "scholar_id", "work_title", "school", "argues_about", "stance", "evidence_line_id"],
    }.items():
        write_table(name, [], cols)

    # manifest
    tables = []
    for f in sorted(OUT_DIR.glob("*.parquet")):
        try:
            n = len(pd.read_parquet(f))
        except Exception:
            n = -1
        tables.append({"name": f.stem, "path": f.name, "rows": n, "size_bytes": f.stat().st_size})

    manifest = {
        "project": "Journey-to-the-West Knowledge Graph",
        "version": "0.1.0",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ontology": "../03_本体论规范/jtw_kg_ontology.ttl",
        "vocabularies": "../03_本体论规范/vocabularies.yaml",
        "source_extract_dir": str(EXTRACT_DIR.relative_to(ROOT)),
        "counts": {
            "pages": len(data["pages"]),
            "lines": len(data["lines"]),
            "entities": len(data["entities"]),
            "relationships": len(data["relationships"]),
            "events": len(data["events"]),
            "mentions": len(data["mentions"]),
            "annotations": len(data["annotations"]),
            "chapters": len(chapters),
            "editions": len(EDITIONS_SEED),
        },
        "tables": tables,
        "status": "skeleton_v0.1",
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"[manifest] {OUT_DIR/'manifest.json'}")
    log(f"[done] {len(tables)} tables, "
        f"pages={len(data['pages'])} lines={len(data['lines'])} "
        f"entities={len(data['entities'])} chapters={len(chapters)}")


if __name__ == "__main__":
    main()
