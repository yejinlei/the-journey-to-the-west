#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RapidOCR 本地快速 OCR 封装。

用途：
1. 一次性把所有 PDF/JPG 页提取为纯文本，作为 base layer
2. 给 VLM 管线做交叉验证（VLM 抽完后再比对 RapidOCR 结果）
3. 对 VLM 抽取失败的页面做兜底

用法：
    from rapid_ocr_engine import RapidOCREngine
    engine = RapidOCREngine()
    text = engine.ocr_image("p0050.jpg")
    text = engine.ocr_pdf("book.pdf")
"""
import os
import sys
import time
from pathlib import Path

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception as e:
    raise RuntimeError(f"rapidocr_onnxruntime 未安装: {e}")

try:
    import fitz  # PyMuPDF
except Exception as e:
    fitz = None


class RapidOCREngine:
    def __init__(self):
        self._ocr = None
        self._warmup = False

    def _ensure(self):
        if self._ocr is None:
            self._ocr = RapidOCR()
        return self._ocr

    def ocr_image(self, image_path, dpi=None):
        """对单张图 OCR，返回 {text, boxes, confidence, elapsed}。"""
        t0 = time.time()
        ocr = self._ensure()
        img = str(image_path)
        # RapidOCR 接受路径或 numpy array
        result, elapse = ocr(img)
        dt = time.time() - t0
        if not result:
            return {"text": "", "boxes": [], "confidence": 0.0, "elapsed": dt,
                    "raw": None}
        texts = []
        boxes = []
        confs = []
        for item in result:
            box, txt, conf = item[0], item[1], item[2]
            texts.append(txt)
            boxes.append([[float(p[0]), float(p[1])] for p in box])
            confs.append(float(conf))
        return {
            "text": "\n".join(texts),
            "boxes": boxes,
            "confidence": sum(confs) / max(len(confs), 1),
            "elapsed": dt,
            "raw": result,
        }

    def ocr_pdf(self, pdf_path, max_pages=None, dpi=200, rotate=None):
        """对 PDF 逐页 OCR，返回 {pages:[{page_no, text, confidence, elapsed}], total_text}。

        rotate: 0/90/180/270 强制旋转；None 表示按 PDF 页自身 rotation 元数据。
        """
        if fitz is None:
            raise RuntimeError("PyMuPDF 未安装，请 pip install pymupdf")
        t0 = time.time()
        ocr = self._ensure()
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_out = []
        for i in range(total_pages):
            if max_pages and i >= max_pages:
                break
            page = doc[i]
            rot = rotate if rotate is not None else page.rotation
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            # 用 PIL 手动应用 rotate（fitz 只对元数据 rotate 生效）
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                if rot == 90:
                    img = img.rotate(-90, expand=True)
                elif rot == 180:
                    img = img.rotate(180, expand=True)
                elif rot == 270:
                    img = img.rotate(90, expand=True)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                img_bytes = buf.getvalue()
            except Exception:
                img_bytes = pix.tobytes("png")
            result, _ = ocr(img_bytes)
            if not result:
                pages_out.append({"page_no": i + 1, "text": "",
                                   "confidence": 0.0, "elapsed": 0.0})
                continue
            texts = [r[1] for r in result]
            confs = [float(r[2]) for r in result]
            pages_out.append({
                "page_no": i + 1,
                "text": "\n".join(texts),
                "confidence": sum(confs) / len(confs),
                "elapsed": 0.0,
            })
        doc.close()
        return {
            "pages": pages_out,
            "total_pages": total_pages,
            "total_text": "\n\n".join(p["text"] for p in pages_out),
            "elapsed": time.time() - t0,
        }

    def warm(self):
        if not self._warmup:
            self._ensure()
            self._warmup = True


def quick_probe():
    """对一张已知存在的图快速验证。"""
    sample = r"f:\src\The-Journey-to-the-West\book\scans\新刻全像批评西游记\p0050.jpg"
    if not os.path.exists(sample):
        print("样本不存在"); return
    eng = RapidOCREngine()
    r = eng.ocr_image(sample)
    print(f"耗时 {r['elapsed']:.1f}s, 置信度 {r['confidence']:.3f}")
    print(f"文本长度 {len(r['text'])}")
    print("--- 前 300 字符 ---")
    print(r['text'][:300])


if __name__ == "__main__":
    quick_probe()
