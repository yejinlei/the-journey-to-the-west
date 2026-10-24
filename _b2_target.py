import re
SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n(.*?)(?=\n===|\Z)', SRC, re.S):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    PAGES[p] = ws

total_lines = 0
for p in [20,21,22,23,25,26,28,30,32,33,34]:
    ws = PAGES[p]
    print(f"p{p}: nlines={len(ws)}, sum={sum(ws)}")
    total_lines += len(ws)
print("TOTAL LINES:", total_lines)
