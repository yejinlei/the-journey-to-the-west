#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接入 yejinlei/pdf-ocr-skill 的 PDF 底稿抽取层。

策略：
1. 复用 pdf-ocr-skill 提供的 PDFOCRProcessor / RapidOCREngine（三引擎抽象）
2. 采用"流式逐页"处理，把 PyMuPDF 单页 pixmap 直接喂给 skill 的 RapidOCR
3. 输出：
   - book/extract/pdf-ocr-raw/{edition}/page_{N:04d}.txt   每页纯文本
   - book/extract/pdf-ocr-raw/{edition}/pages.jsonl        每页索引（可追加、可断点续传）
4. 后续 hook：可挂 VLM 交叉验证 / 疑难页兜底（当 skill 引擎返回空或置信度过低）

用法：
    python pdf_ocr_skill.py <pdf_path> --edition shidetang [--start 1 --end 10] [--dpi 180] [--engine rapid]
"""
import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# ── 加载 pdf-ocr-skill ─────────────────────────────────────────
SKILL_DIR = r"c:\Users\T480\.trae-cn\skills\pdf-ocr-skill"
SKILL_SCRIPTS = os.path.join(SKILL_DIR, "scripts")
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

try:
    from pdf_ocr_processor import PDFOCRProcessor, RapidOCREngine as SkillRapidEngine
    SKILL_OK = True
except Exception as e:
    SKILL_OK = False
    SKILL_ERR = str(e)

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

OUT_ROOT = Path(r"f:\src\The-Journey-to-the-West\book\extract\pdf-ocr-raw")
LOG_DIR = Path(r"f:\src\The-Journey-to-the-West\book\extract\_logs")


def setup_logging(edition: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"pdf_ocr_skill_{edition}.log"
    logger = logging.getLogger(f"pdf_ocr_skill.{edition}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    sh = logging.StreamHandler()
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    sh.setFormatter(fmt)
    fh.setFormatter(fmt)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


def stream_extract(pdf_path: str, edition: str,
                   engine: str = "rapid", dpi: int = 180,
                   start_page: int = 1, end_page: Optional[int] = None,
                   overwrite: bool = False) -> dict:
    """流式逐页抽取 PDF 文本底稿。

    - engine: rapid / rapidoc / siliconflow（默认 rapid 本地）
    - 支持断点续传：page_{N:04d}.txt 已存在则跳过（除非 overwrite=True）
    """
    logger = setup_logging(edition)
    if not SKILL_OK:
        logger.error(f"pdf-ocr-skill 加载失败：{SKILL_ERR}")
        raise RuntimeError(f"pdf-ocr-skill 不可用：{SKILL_ERR}")
    if fitz is None:
        raise RuntimeError("PyMuPDF 未安装")

    edition_dir = OUT_ROOT / edition
    edition_dir.mkdir(parents=True, exist_ok=True)
    idx_path = edition_dir / "pages.jsonl"

    # skill 初始化（一次加载引擎，多次调用）
    logger.info(f"[init] engine={engine}, dpi={dpi}")
    t_init = time.time()
    processor = PDFOCRProcessor(engine=engine)
    engine_used = processor.engine_type  # skill 内部可能自动 fallback
    logger.info(f"[init] 实际引擎：{engine_used}  耗时 {time.time()-t_init:.1f}s")

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    if end_page is None:
        end_page = total_pages
    start_page = max(1, min(start_page, total_pages))
    end_page = max(start_page, min(end_page, total_pages))
    logger.info(f"[range] {pdf_path}")
    logger.info(f"[range] 总页 {total_pages}，处理 {start_page}-{end_page}")

    written = 0
    skipped = 0
    failed = []
    t_all = time.time()

    # 单页临时文件目录（skill 的 recognize() 需要路径）
    tmp_dir = edition_dir / "_tmp"
    tmp_dir.mkdir(exist_ok=True)

    with open(idx_path, "a", encoding="utf-8") as fj:
        for i in range(start_page, end_page + 1):
            page_no = i
            txt_path = edition_dir / f"page_{page_no:04d}.txt"
            if txt_path.exists() and not overwrite:
                skipped += 1
                continue

            t0 = time.time()
            try:
                page = doc[page_no - 1]
                pix = page.get_pixmap(dpi=dpi, alpha=False)
                img_bytes = pix.tobytes("png")
                tmp_img = tmp_dir / f"p{page_no:04d}.png"
                tmp_img.write_bytes(img_bytes)

                # ── skill 引擎分发 ──
                text = ""
                if engine_used == "rapid" and processor.rapid_engine:
                    # skill RapidOCR: recognize(image_path) -> str
                    text = processor.rapid_engine.recognize(str(tmp_img))
                elif engine_used == "rapidoc" and processor.rapidoc_engine:
                    r = processor.rapidoc_engine.recognize(str(tmp_img))
                    text = r.get("text", "")
                elif engine_used == "siliconflow" and processor.siliconflow_engine:
                    import base64
                    b64 = base64.b64encode(img_bytes).decode()
                    text = processor.siliconflow_engine.recognize(b64, page_no)

                tmp_img.unlink(missing_ok=True)

                with open(txt_path, "w", encoding="utf-8") as fw:
                    fw.write(text)

                chars = len(text.replace("\n", "").replace(" ", ""))
                dt = time.time() - t0
                written += 1
                logger.info(f"  p{page_no:04d}  {chars:>5}字  {dt:>5.1f}s")

                # 追加索引
                fj.write(json.dumps({
                    "edition": edition,
                    "pdf": pdf_path,
                    "page_no": page_no,
                    "chars": chars,
                    "engine": engine_used,
                    "dpi": dpi,
                    "elapsed_sec": round(dt, 2),
                    "text_path": str(txt_path),
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }, ensure_ascii=False) + "\n")
                fj.flush()
            except Exception as e:
                failed.append((page_no, str(e)))
                logger.error(f"  p{page_no:04d} FAILED: {e}")

    doc.close()
    total_dt = time.time() - t_all
    summary = {
        "edition": edition,
        "pdf": pdf_path,
        "engine": engine_used,
        "range": [start_page, end_page],
        "written": written,
        "skipped": skipped,
        "failed": len(failed),
        "elapsed_sec": round(total_dt, 1),
        "avg_sec_per_page": round(total_dt / max(written, 1), 2),
        "out_dir": str(edition_dir),
    }
    logger.info(f"[done] {summary}")
    return summary


def run_all_pdfs(edition_map: dict, dpi: int = 180, engine: str = "rapid",
                 start_page: int = 1, end_page: Optional[int] = None):
    """批量抽取多个 PDF。edition_map = {edition_name: pdf_path}"""
    results = {}
    for edition, pdf_path in edition_map.items():
        if not os.path.exists(pdf_path):
            print(f"[skip] PDF 不存在: {pdf_path}")
            continue
        results[edition] = stream_extract(pdf_path, edition, engine=engine,
                                          dpi=dpi, start_page=start_page,
                                          end_page=end_page)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="pdf-ocr-skill 接入层")
    ap.add_argument("pdf", nargs="?", help="PDF 路径；不传则自动扫描 book/scans/**.pdf")
    ap.add_argument("--edition", default=None, help="版本标识（如 shidetang）")
    ap.add_argument("--engine", default="rapid", choices=["rapid", "rapidoc", "siliconflow"])
    ap.add_argument("--dpi", type=int, default=180)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--all-pdfs", action="store_true", help="扫描所有 PDF 全部处理")
    args = ap.parse_args()

    scans_root = r"f:\src\The-Journey-to-the-West\book\scans"

    if args.all_pdfs:
        pdf_map = {}
        for p in Path(scans_root).rglob("*.pdf"):
            edition = p.parent.name
            pdf_map[edition] = str(p)
        print(f"发现 {len(pdf_map)} 个 PDF：")
        for k, v in pdf_map.items():
            print(f"  [{k}] {v}")
        run_all_pdfs(pdf_map, dpi=args.dpi, engine=args.engine,
                     start_page=args.start, end_page=args.end)
    elif args.pdf:
        if not args.edition:
            args.edition = Path(args.pdf).parent.name
        stream_extract(args.pdf, args.edition, engine=args.engine, dpi=args.dpi,
                       start_page=args.start, end_page=args.end,
                       overwrite=args.overwrite)
    else:
        ap.print_help()
        sys.exit(1)
