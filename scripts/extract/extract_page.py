#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单页抽取：OCR 分层 → 实体/关系抽取 → JSON-LD 落盘。

用法：
    python extract_page.py <page_image_path> <edition_dir_name> <page_no>

断点续传：若目标 JSON-LD 已存在，直接返回。
"""
import os, sys, json, re, time, argparse, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SENSENOVA_API_KEY", "sk-MUdQGuADpncGwjHHPSjLAqWFTlnZUfUI")

from vlm_client import vlm_chat, image_messages, text_messages
from schema import (
    EDITIONS, SYSTEM_OCR, SYSTEM_ANNOTATE, USER_OCR, USER_ANNOTATE,
    page_uri, page_record_meta, new_uri, now_iso,
)

ROOT = r"f:\src\The-Journey-to-the-West\book\scans"
OUT_ROOT = r"f:\src\The-Journey-to-the-West\book\extract"

# 稳定 hash（避免依赖 uuid 顺序）
def stable_hash(s: str) -> str:
    import hashlib
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def parse_json_response(text: str):
    """从 VLM 返回中提取 JSON（容忍开头空白/代码围栏/多余字符）。"""
    if not text:
        return None
    t = text.strip()
    # 去掉 ```json ... ``` 围栏
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)
    t = t.strip()
    # 尝试直接 parse
    try:
        return json.loads(t)
    except Exception:
        pass
    # 兜底：找首个 { ... 对应 }
    start = t.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(t)):
        c = t[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(t[start:i+1])
                except Exception:
                    return None
    return None


def extract_ocr(image_path: str):
    """第一步：OCR 分层。"""
    t0 = time.time()
    raw = vlm_chat(image_messages(SYSTEM_OCR, USER_OCR, [image_path]),
                   max_tokens=8000, timeout=300)
    dt = time.time() - t0
    obj = parse_json_response(raw)
    return obj, raw, dt


def extract_annotation(ocr_obj: dict):
    """第二步：根据 OCR lines 抽实体。"""
    lines_json = json.dumps(ocr_obj.get("lines", []), ensure_ascii=False)
    user = USER_ANNOTATE.format(lines_json=lines_json)
    t0 = time.time()
    raw = vlm_chat(text_messages(SYSTEM_ANNOTATE, user),
                   max_tokens=6000, timeout=300)
    dt = time.time() - t0
    obj = parse_json_response(raw)
    return obj, raw, dt


def assemble_jsonld(image_path, edition_dir, page_no, page_index,
                    ocr_obj, anno_obj, timings):
    edition_code, edition_name = EDITIONS.get(edition_dir, (edition_dir, edition_dir))
    page_id = page_uri(edition_code, page_no)
    record = page_record_meta(page_id, os.path.relpath(image_path, ROOT),
                              edition_code, edition_name, page_no, page_index)

    # OCR 结构
    record["jtw:ocr"] = {
        "layout": (ocr_obj or {}).get("layout", "unknown"),
        "lines": (ocr_obj or {}).get("lines", []),
        "page_meta": (ocr_obj or {}).get("page_meta", {}),
    }
    record["jtw:annotation"] = anno_obj or {}

    # 汇总统计
    lines = (ocr_obj or {}).get("lines", [])
    anno = anno_obj or {}
    record["jtw:stats"] = {
        "line_count": len(lines),
        "commentary_line_count": sum(
            1 for L in lines
            if L.get("type") in ("inline", "top", "side", "bottom", "pre", "post")
        ),
        "main_line_count": sum(1 for L in lines if L.get("type") == "main"),
        "title_line_count": sum(1 for L in lines if L.get("type") == "title"),
        "entity_count": len(anno.get("entities", [])),
        "relation_count": len(anno.get("relationships", [])),
        "event_count": len(anno.get("events", [])),
        "chapter_ref": anno.get("chapter_ref", ""),
    }

    # 生成稳定实体 URI，便于跨页聚合
    entities_out = []
    for e in anno.get("entities", []):
        eid = e.get("id") or stable_hash(e.get("canonical_name", e.get("label", "")))
        e_out = dict(e)
        e_out["@id"] = f"http://xjy.ontology.local/entity/{edition_code}/{eid}"
        e_out["jtw:entityType"] = e.get("type")
        entities_out.append(e_out)
    record["jtw:entities"] = entities_out

    # 关系 & 事件
    record["jtw:relationships"] = anno.get("relationships", [])
    record["jtw:events"] = anno.get("events", [])

    # 处理时间戳
    record["jtw:timings"] = timings
    record["dct:created"] = now_iso()
    record["jtw:schemaVersion"] = "1.0.0"
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="+")
    ap.add_argument("--edition-dir", default=None,
                    help="书格目录名（如'李评本'、'大奇书本_Gallica4040'）。默认取 image[0] 的父目录名。")
    ap.add_argument("--page-index", type=int, default=None,
                    help="同一版本内的页序（1-based），用于断点续传与汇总。默认从文件名 p0123 解析。")
    args = ap.parse_args()

    os.makedirs(OUT_ROOT, exist_ok=True)

    for image_path in args.image:
        if not os.path.exists(image_path):
            print(f"跳过不存在的图片: {image_path}")
            continue

        edition_dir = args.edition_dir or os.path.basename(os.path.dirname(os.path.abspath(image_path)))
        fname = os.path.basename(image_path)
        m = re.search(r"(\d+)", fname)
        page_no = args.page_index or (int(m.group(1)) if m else 0)

        out_path = os.path.join(OUT_ROOT, edition_dir, f"p{page_no:05d}.jsonld")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        # 断点续传
        if os.path.exists(out_path):
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    _ = json.load(f)
                print(f"[SKIP] {out_path}")
                continue
            except Exception:
                pass  # 损坏则重跑

        print(f"[OCR ] {image_path} (edition={edition_dir} page={page_no})")
        try:
            ocr_obj, ocr_raw, dt_ocr = extract_ocr(image_path)
            if not ocr_obj:
                print(f"    OCR 解析失败，返回原文：{ocr_raw[:200]!r}")
                ocr_obj = {"layout": "parse_failed", "lines": [],
                           "page_meta": {"notes": "OCR JSON 解析失败", "raw": ocr_raw[:2000]}}
            print(f"    OCR {dt_ocr:.1f}s lines={len(ocr_obj.get('lines', []))}")
        except Exception as e:
            print(f"    OCR 失败: {e}")
            traceback.print_exc()
            continue

        print(f"[ANN ] 实体抽取 ...")
        try:
            anno_obj, anno_raw, dt_anno = extract_annotation(ocr_obj)
            if not anno_obj:
                print(f"    ANN 解析失败: {anno_raw[:200]!r}")
                anno_obj = {"entities": [], "relationships": [], "events": [],
                            "confidence": 0.0}
            print(f"    ANN {dt_anno:.1f}s "
                  f"ents={len(anno_obj.get('entities', []))} "
                  f"rels={len(anno_obj.get('relationships', []))} "
                  f"events={len(anno_obj.get('events', []))}")
        except Exception as e:
            print(f"    ANN 失败: {e}")
            anno_obj = {"entities": [], "relationships": [], "events": [], "confidence": 0.0}
            dt_anno = 0.0

        timings = {"ocr_seconds": round(dt_ocr, 2), "annotation_seconds": round(dt_anno, 2)}
        record = assemble_jsonld(image_path, edition_dir, page_no, page_no,
                                 ocr_obj, anno_obj, timings)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # 追加写 JSONL 索引（仅在保存成功后）
        jsonl_path = os.path.join(OUT_ROOT, edition_dir, "pages.jsonl")
        with open(jsonl_path, "a", encoding="utf-8") as fj:
            fj.write(json.dumps({
                "path": image_path,
                "edition": edition_dir,
                "page_no": page_no,
                "jsonld": out_path,
                "line_count": record["jtw:stats"]["line_count"],
                "commentary_line_count": record["jtw:stats"]["commentary_line_count"],
                "entity_count": record["jtw:stats"]["entity_count"],
                "relation_count": record["jtw:stats"]["relation_count"],
                "event_count": record["jtw:stats"]["event_count"],
                "chapter_ref": record["jtw:stats"]["chapter_ref"],
                "ts": now_iso(),
            }, ensure_ascii=False) + "\n")
        print(f"[SAVE] {out_path}")


if __name__ == "__main__":
    main()
