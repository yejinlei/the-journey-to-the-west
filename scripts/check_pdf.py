#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查 PDF 古籍扫描件的页数与图像分辨率（只读元数据，不解码像素）。

  py -3 scripts/check_pdf.py "book/scans/世德堂本/xxx.pdf"
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import pypdf
except ImportError:
    print("需要 pypdf：py -3 -m pip install pypdf")
    sys.exit(1)

path = sys.argv[1] if len(sys.argv) > 1 else \
    "book/scans/世德堂本/新刻出像官板大字西游记.世德堂本.灰度胶片.pdf"
p = Path(path)
if not p.exists():
    print("文件不存在: %s" % p)
    sys.exit(1)

print("文件: %s" % p.name)
print("体积: %.2f GB" % (p.stat().st_size / 1073741824))

reader = pypdf.PdfReader(str(p))
n = len(reader.pages)
print("页数: %d" % n)

idxs = [0]
if n > 1:
    idxs.append(n // 2)
if n > 2:
    idxs.append(n - 1)

for i in idxs:
    page = reader.pages[i]
    mb = page.mediabox
    w_pt = float(mb.width)
    h_pt = float(mb.height)
    w_in = w_pt / 72.0
    h_in = h_pt / 72.0
    info = []
    try:
        res = page.get("/Resources")
        xo = res.get("/XObject") if res else None
        if xo:
            for name, obj in xo.get_object().items():
                o = obj.get_object()
                if o.get("/Subtype") == "/Image":
                    iw = o.get("/Width")
                    ih = o.get("/Height")
                    filt = o.get("/Filter")
                    bpc = o.get("/BitsPerComponent")
                    dpi = (iw / w_in) if (iw and w_in) else 0
                    info.append("%sx%s  %sbit  %s  ~%.0f dpi"
                                % (iw, ih, bpc, str(filt)[:18], dpi))
    except Exception as e:
        info.append("解析失败: %s" % str(e)[:60])
    print("\n第 %d 页  版面 %.0fx%.0f pt (%.1f x %.1f inch)"
          % (i + 1, w_pt, h_pt, w_in, h_in))
    for s in info[:4]:
        print("    " + s)
