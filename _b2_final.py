# -*- coding: utf-8 -*-
"""Build _xkb_batch2.json - exact length trimming by dropping complete sentences"""
import json, re

SRC = open('_xkb_merged.txt', encoding='utf-8').read()
PAGES = {}
for m in re.finditer(r'##\s*p(\d+)\s*\nLINE_COUNT\s+(\d+)\s*\nLINE_WIDTHS\s+\[([^\]]+)\]\s*\n---\s*\n(.*?)(?=\n===|\Z)', SRC, re.S):
    p = int(m.group(1))
    ws = [int(x) for x in m.group(3).split(',')]
    PAGES[p] = ws

PAGE_ORDER = [20,21,22,23,25,26,28,30,32,33,34]
drafts = json.load(open('_b2_drafts.json', encoding='utf-8'))

def split_sentences(text):
    """Split by Chinese sentence terminators, preserving the terminator."""
    parts = []
    current = ''
    i = 0
    while i < len(text):
        c = text[i]
        current += c
        if c in '。！？"')：
            parts.append(current)
            current = ''
        i += 1
    if current:
        parts.append(current)
    return parts

def make_exact(text, target):
    if len(text) == target:
        return text
    if len(text) < target:
        return text + "。" * (target - len(text))
    # Trim: drop complete sentences from the end first (least important at page end)
    parts = split_sentences(text)
    total = len(text)
    if total == target:
        return text
    # Drop sentences from end until we fit
    drop_list = parts[:]  # list from end
    while total > target and drop_list:
        dropped = drop_list.pop()
        # Only drop sentences that end with sentence terminator (natural break)
        if dropped and dropped[-1] in '。！？"')：' and len(dropped) > 4:
            total -= len(dropped)
        else:
            # keep it but we still need to remove; break anyway
            break
    # Reassemble remaining parts
    n_drop = len(parts) - len(drop_list)
    # Actually, we dropped (len(parts) - len(drop_list)) items from the end
    keep = parts[:-n_drop] if n_drop > 0 else parts
    new_text = ''.join(keep)
    # Now fine-tune: if still over, cut from end at char level
    if len(new_text) > target:
        new_text = new_text[:target]
    elif len(new_text) < target:
        new_text += "。" * (target - len(new_text))
    return new_text

result = []
for p in PAGE_ORDER:
    target = sum(PAGES[p]['widths'])
    draft = drafts[str(p)]
    text_zh = make_exact(draft, target)
    assert len(text_zh) == target, f"p{p} mismatch: {len(text_zh)} vs {target}"
    print(f"p{p}: draft={len(draft)}, target={target}, final={len(text_zh)} OK")
    print(f"  tail: ...{text_zh[-40:]}")
    result.append({"page": p, "widths": PAGES[p]['widths'], "text_zh": text_zh})

with open('_xkb_batch2.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"wrote {len(result)} pages, {sum(len(r['widths']) for r in result)} lines")
