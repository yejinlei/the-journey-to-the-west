#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 逐页 OCR 批量抽取（RapidOCR 引擎）。

产出：
  book/extract/pdf-ocr-raw/{edition}/page_{N:04d}.txt  每页纯文本
  book/extract/pdf-ocr-raw/{edition}/pages.jsonl        索引（每行 {page_no, chars, confidence, path}）

用法：
  python pdf_ocr_batch.py <pdf_path> --edition shidetang
"""
import os, sys, json, argparse, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rapid_ocr_engine import RapidOCREngine

OUT_ROOT = r"f:\src\The-Journey-to-the-West\book\extract\pdf-ocr-raw"

def process(pdf_path, edition, max_pages=None, dpi=180, workers=None):
    os.makedirs(os.path.join(OUT_ROOT, edition), exist_ok=True)
    engine = RapidOCREngine()
    print(f"[PDF] {pdf_path}")
    t0 = time.time()
    result = engine.ocr_pdf(pdf_path, max_pages=max_pages, dpi=dpi)
    dt = time.time() - t0
    print(f"  总页数 {result['total_pages']}  耗时 {dt:.1f}s  ({dt/max(result['total_pages'],1):.1f}s/页)")

    idx_path = os.path.join(OUT_ROOT, edition, "pages.jsonl")
    with open(idx_path, "a", encoding="utf-8") as fj:
        for p in result["pages"]:
            txt = p["text"]
            pageno = p["page_no"]
            txt_path = os.path.join(OUT_ROOT, edition, f"page_{pageno:04d}.txt")
            with open(txt_path, "w", encoding="utf-8") as fw:
                fw.write(txt)
            chars = len(txt.replace("\n", "").replace(" ", ""))
            fj.write(json.dumps({
                "edition": edition,
                "pdf": pdf_path,
                "page_no": pageno,
                "chars": chars,
                "confidence": round(p.get("confidence", 0.0), 3),
                "text_path": txt_path,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }, ensure_ascii=False) + "\n")
    print(f"  已保存 {len(result['pages'])} 页到 {OUT_ROOT}/{edition}/")
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--edition", required=True)
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--dpi", type=int, default=180)
    args = ap.parse_args()
    process(args.pdf, args.edition, args.max_pages, args.dpi)


if __name__ == "__main__":
    main()
