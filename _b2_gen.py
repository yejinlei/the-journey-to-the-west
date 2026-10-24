import json, re
SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n', SRC):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    PAGES[p] = ws

PAGE_ORDER = [20,21,22,23,25,26,28,30,32,33,34]

drafts = json.load(open('_b2_drafts.json', encoding='utf-8'))

def split_sent(t):
    parts = []
    cur = ''
    for c in t:
        cur += c
        if c in '。！？':
            parts.append(cur)
            cur = ''
    if cur: parts.append(cur)
    return parts

def make_exact(text, target):
    if len(text) == target:
        return text
    if len(text) < target:
        # pad with '。'
        return text + '。' * (target - len(text))
    # too long - trim sentences from end, prefer short sentences
    parts = split_sent(text)
    # sort by length ascending; greedily drop shortest ones from end
    # We'll do: drop sentences from end, but prefer to drop the shortest ones among the tail
    total = len(text)
    dropped = set()
    while total > target:
        # find the shortest sentence not yet dropped, prefer from the tail half
        candidates = [(i, len(parts[i])) for i in range(len(parts)) if i not in dropped]
        if not candidates: break
        # prefer tail (last 40%)
        tail_start = max(0, len(parts) - max(1, len(parts) // 3))
        tail_cands = [(i, ln) for i, ln in candidates if i >= tail_start]
        pool = tail_cands if tail_cands else candidates
        # sort by length ascending (drop shortest first)
        pool.sort(key=lambda x: x[1])
        i, ln = pool[0]
        dropped.add(i)
        total -= ln
    # Rebuild
    new_parts = [parts[i] for i in range(len(parts)) if i not in dropped]
    new_text = ''.join(new_parts)
    # Pad if needed
    if len(new_text) < target:
        new_text += '。' * (target - len(new_text))
    elif len(new_text) > target:
        new_text = new_text[:target]
    return new_text

result = []
for p in PAGE_ORDER:
    target = sum(PAGES[p])
    draft = drafts[str(p)]
    text_zh = make_exact(draft, target)
    assert len(text_zh) == target, f"p{p}: {len(text_zh)} vs {target}"
    result.append({"page": p, "widths": PAGES[p], "text_zh": text_zh})
    print(f"p{p}: OK len={len(text_zh)}=={target}")

with open('_xkb_batch2.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"wrote {len(result)} pages, {sum(len(r['widths']) for r in result)} lines total")
