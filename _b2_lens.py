import json, re
drafts = json.load(open('_b2_drafts.json', encoding='utf-8'))
SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n(.*?)(?=\n===|\Z)', SRC, re.S):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    PAGES[p] = ws

for p in [20,21,22,23,25,26,28,30,32,33,34]:
    dl = len(drafts[str(p)])
    target = sum(PAGES[p])
    diff = target - dl
    print('p%d: draft_len=%d, target=%d, diff=%d' % (p, dl, target, diff))
