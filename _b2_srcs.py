import re
SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n(.*?)(?=\n===|\Z)', SRC, re.S):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    body = m.group(4).strip()
    PAGES[p] = {'widths': ws, 'body': body}

lines_out = []
for p in [20,21,22,23,25,26,28,30,32,33,34]:
    info = PAGES[p]
    lines_out.append(f"=== p{p}: sum={sum(info['widths'])} ===")
    lines_out.append(info['body'])
    lines_out.append("")

with open('_b2_srcs_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines_out))
print("wrote _b2_srcs_out.txt")
