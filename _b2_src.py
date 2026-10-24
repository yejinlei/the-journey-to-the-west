import re
SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n(.*?)(?=\n===|\Z)', SRC, re.S):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    body = m.group(4).strip()
    PAGES[p] = {'widths': ws, 'body': body}

for p in [20,21,22,23,25,26,28,30,32,33,34]:
    info = PAGES[p]
    print(f"=== p{p}: nlines={len(info['widths'])}, sum={sum(info['widths'])}, body_len={len(info['body'])} ===")
    print(info['body'][:800])
    print()
