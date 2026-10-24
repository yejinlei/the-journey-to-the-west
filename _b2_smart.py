import json, re
drafts = json.load(open('_b2_drafts.json', encoding='utf-8'))

# Test: for each page, drop sentences from end with size <= 40 chars until close to target
def split_sent(t):
    parts = []
    cur = ''
    for c in t:
        cur += c
        if c in '。！？':
            parts.append(cur)
            cur = ''
    if cur:
        parts.append(cur)
    return parts

SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n(.*?)(?=\n===|\Z)', SRC, re.S):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    PAGES[p] = ws

PAGE_ORDER = [20,21,22,23,25,26,28,30,32,33,34]

for p in PAGE_ORDER:
    target = sum(PAGES[p]['widths'])
    text = drafts[str(p)]
    parts = split_sent(text)
    print(f"\n=== p{p}: draft={len(text)}, target={target}, need_drop={len(text)-target} ===")
    print(f"  parts count: {len(parts)}")
    # Print each part's length and last char
    for i, pt in enumerate(parts):
        print(f"  [{i}] len={len(pt)} tail='{pt[-15:]}'")
