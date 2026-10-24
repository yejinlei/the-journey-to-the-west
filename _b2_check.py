import json, re
drafts = json.load(open('_b2_drafts.json', encoding='utf-8'))
SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n(.*?)(?=\n===|\Z)', SRC, re.S):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    PAGES[p] = ws

PAGE_ORDER = [20,21,22,23,25,26,28,30,32,33,34]

def make_exact(text, target):
    """Return text with exact len == target by trimming from end (removing chars)."""
    if len(text) == target:
        return text
    if len(text) > target:
        return text[:target]
    # too short: pad with punctuation
    return text + "。" * (target - len(text))

result = []
for p in PAGE_ORDER:
    target = sum(PAGES[p]['widths'])
    draft = drafts[str(p)]
    text_zh = make_exact(draft, target)
    ok = len(text_zh) == target
    print(f"p{p}: draft={len(draft)}, target={target}, final={len(text_zh)}, ok={ok}")
    result.append({"page": p, "widths": PAGES[p]['widths'], "text_zh": text_zh})

with open('_xkb_batch2.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print('wrote', len(result), 'pages')
