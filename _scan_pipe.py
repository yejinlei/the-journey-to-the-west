import json, glob, re
from pathlib import Path

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
# 扫描包含 "|" 的行（排除常见标点：全角｜等）
pipe_lines = []
for l in d['lines']:
    for fld in ('text', 'text_zh'):
        v = l.get(fld) or ''
        # ASCII 管道符 |
        if re.search(r'\s\|\s', v) or re.search(r'\|.*=\s', v):
            pipe_lines.append((l['edition'], l['page_no'], l['line_idx'], fld, v))

print(f"含 ASCII | 且形似管道的行: {len(pipe_lines)}")
for e, p, i, f, v in pipe_lines[:40]:
    print(f"  [{e}] p{p}#{i} {f}: {v[:150]!r}")
