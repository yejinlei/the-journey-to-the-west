#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建期静态渲染：把只读页面所需的数据用本地 DuckDB 从 parquet 跑成 JSON，
输出到 docs/data/pages/*.json。前端 fetch JSON 直接渲染，无需 wasm。

用法：
    python 05_构建脚本/export_pages.py

幂等：每次覆盖写。
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb

# ---------------- 路径 ----------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "04_knowledge_data"          # 输入：parquet 源
OUT_DIR = ROOT / "docs" / "data" / "pages"     # 输出：页面 JSON
MANIFEST_OUT = ROOT / "docs" / "data" / "pages" / "_manifest.json"

# ---------------- 页面查询（与前端原 SQL 一一对应）----------------
PAGE_QUERIES: dict[str, dict[str, str]] = {
    "read": {
        "editions": (
            'SELECT edition_id, display_name, publisher, "desc" FROM editions '
            "WHERE edition_id IN ('xinke_pingbi','gubao','baihui_xiangzhu') "
            "ORDER BY edition_id"
        ),
        "chapters": (
            "SELECT chapter_id, edition, chapter_label, chapter_title, "
            "first_page, first_line_id FROM chapters "
            "WHERE edition IN ('xinke_pingbi','gubao','baihui_xiangzhu') "
            "ORDER BY edition, first_page"
        ),
        "lines": (
            "SELECT page_id, page_no, line_idx, form_type, text, "
            "char_count, is_commentary, edition FROM lines "
            "WHERE edition IN ('xinke_pingbi','gubao','baihui_xiangzhu') "
            "ORDER BY edition, page_no, line_idx"
        ),
        "annotations": (
            "SELECT page_id, page_no, line_idx, form_type, text, "
            "confidence, chapter_ref, edition FROM annotations "
            "WHERE edition='xinke_pingbi' ORDER BY page_no, line_idx"
        ),
    },
    "entities": {
        "entities": (
            "SELECT entity_id, entity_id_raw, type, label, canonical_name, "
            "aliases, mention_count FROM entities ORDER BY type, mention_count DESC"
        ),
    },
    "versions": {
        "editions": (
            'SELECT edition_id, display_name, year, publisher, "desc" FROM editions '
            "ORDER BY CASE WHEN year > 0 THEN 0 ELSE 1 END, year, display_name"
        ),
        "annosByCh": (
            "SELECT chapter_ref, count(*) as n FROM annotations "
            "WHERE edition='xinke_pingbi' GROUP BY 1 ORDER BY 1"
        ),
    },
    "relics": {
        "artifacts": (
            "SELECT entity_id, entity_id_raw, label, canonical_name, aliases, "
            "mention_count FROM entities WHERE type='artifact' ORDER BY mention_count DESC"
        ),
        "hasWeapon": (
            "SELECT subject_id, predicate, object_id, evidence, line_idx "
            "FROM relationships WHERE predicate='jtw:hasWeapon'"
        ),
        "entities": (
            "SELECT entity_id, label, canonical_name, type FROM entities"
        ),
    },
    "annotations": {
        "annotations": (
            "SELECT annotation_id, page_no, line_idx, form_type, text, confidence, "
            "chapter_ref FROM annotations WHERE edition='xinke_pingbi' "
            "ORDER BY page_no, line_idx"
        ),
    },
    "events": {
        "events": (
            "SELECT event_id, page_no, name, actor_count, place_label, summary, "
            "line_span, category FROM events WHERE edition='xinke_pingbi' "
            "ORDER BY page_no, line_span"
        ),
    },
    "graph": {
        "rels": (
            "SELECT relation_id, subject_id, predicate, object_id, evidence, page_no "
            "FROM relationships WHERE edition='xinke_pingbi'"
        ),
        "ents": (
            "SELECT entity_id, label, canonical_name, type, mention_count, aliases "
            "FROM entities"
        ),
        "events": (
            "SELECT event_id, page_no, name, summary FROM events "
            "WHERE edition='xinke_pingbi' ORDER BY page_no"
        ),
        "annos": (
            "SELECT page_no, form_type, text FROM annotations "
            "WHERE edition='xinke_pingbi'"
        ),
    },
}


# ---------------- 值序列化 ----------------
def norm(v: Any) -> Any:
    """把 duckdb/pandas 返回的原始值转成 JSON-safe 类型。"""
    if v is None:
        return None
    if isinstance(v, (bool, str, int)):
        return v
    if isinstance(v, float):
        # NaN/Inf → null（JSON 规范不允许）
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        # 保留数值原形；如为整数值就转 int
        f = float(v)
        if f.is_integer():
            return int(f)
        return f
    if hasattr(v, "item"):  # numpy scalar
        try:
            return norm(v.item())
        except Exception:
            pass
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8", errors="replace")
        except Exception:
            return v.hex()
    if isinstance(v, list):
        return [norm(x) for x in v]
    if isinstance(v, tuple):
        return [norm(x) for x in v]
    if isinstance(v, dict):
        return {str(k): norm(x) for k, x in v.items()}
    # fallback：str（含 pandas.NA / pd.Timestamp 等）
    try:
        import pandas as pd
        if pd.isna(v):
            return None
    except Exception:
        pass
    return str(v)


# ---------------- 主流程 ----------------
def build_con() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    for p in sorted(DATA_DIR.glob("*.parquet")):
        tbl = p.stem
        con.execute(f'CREATE OR REPLACE TABLE "{tbl}" AS SELECT * FROM read_parquet(?)', [str(p)])
    return con


def run(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"generated_at": datetime.now().isoformat(timespec="seconds"),
                             "source_dir": str(DATA_DIR), "pages": {}}

    for page, qs in PAGE_QUERIES.items():
        page_data: dict[str, list[dict[str, Any]]] = {}
        for key, sql in qs.items():
            rows = con.execute(sql).fetchall()
            cols = [d[0] for d in con.description]
            data = [
                {c: norm(v) for c, v in zip(cols, row)}
                for row in rows
            ]
            page_data[key] = data
            print(f"  [{page:10s}] {key:12s} -> {len(data):5d} rows")
        result["pages"][page] = page_data

    # 落地每个页面 JSON
    total_kb = 0
    for page, data in result["pages"].items():
        fp = OUT_DIR / f"{page}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        kb = fp.stat().st_size / 1024
        total_kb += kb
        print(f"  => {fp.relative_to(ROOT)}  ({kb:.1f} KB)")
    # 清单
    with open(MANIFEST_OUT, "w", encoding="utf-8") as f:
        json.dump({"generated_at": result["generated_at"], "source_dir": result["source_dir"],
                    "files": list(result["pages"].keys())}, f, ensure_ascii=False, indent=2)
    print(f"\n完成：共 {len(result['pages'])} 个页面 JSON，合计 {total_kb:.1f} KB")
    return result


def main() -> int:
    print(f"数据源：{DATA_DIR}")
    print(f"输出到：{OUT_DIR}\n")
    con = build_con()
    run(con)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
