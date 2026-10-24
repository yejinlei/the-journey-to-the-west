# -*- coding: utf-8 -*-
"""Check character lengths of source text vs LINE_WIDTHS."""
import re

with open('_xkb_merged.txt', 'r', encoding='utf-8') as f:
    content = f.read()

pages = {}
lines = content.split('===\n\n')
for block in lines:
    if not block.strip():
        continue
    m_page = re.search(r'## p(\d+)', block)
    m_widths = re.search(r'LINE_WIDTHS \[([^\]]+)\]', block)
    m_sep = block.find('---')
    if m_page and m_widths and m_sep >= 0:
        page_no = int(m_page.group(1))
        widths = [int(x.strip()) for x in m_widths.group(1).split(',')]
        text = block[m_sep+4:].strip()
        pages[page_no] = {'widths': widths, 'text': text}

for p in [49, 50, 51, 53, 54, 57, 58, 59, 60, 61]:
    if p in pages:
        d = pages[p]
        wsum = sum(d['widths'])
        tlen = len(d['text'])
        print(f"p{p}: len(text)={tlen}, sum(widths)={wsum}, diff={tlen-wsum}, lines={len(d['widths'])}")
        # Show first 100 chars
        print(f"   first 60: {d['text'][:60]!r}")
        print(f"   last 60: {d['text'][-60:]!r}")
        print()
