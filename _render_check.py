"""检查各版本正文/评点渲染：看 form_type 分布 + read.html 是否能匹配"""
import json
from collections import Counter

d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())

# read.html 认识的 form_type: main, title, poem, verse, commentary, caption + fallback
KNOWN_LINES = {'main', 'title', 'poem', 'verse', 'commentary', 'caption'}

for ed in sorted(set(l.get('edition') for l in d['lines'] if l.get('edition'))):
    lines = [l for l in d['lines'] if l.get('edition') == ed]
    cnt = Counter(l.get('form_type') for l in lines)
    unknown = {k: v for k, v in cnt.items() if k not in KNOWN_LINES}
    print(f'=== {ed} ({len(lines)} 行) ===')
    print(f'  form_type 分布: {dict(cnt)}')
    if unknown:
        print(f'  ⚠ 未知 form_type: {unknown}')
        for k, v in unknown.items():
            sample = [l for l in lines if l.get('form_type') == k][:2]
            for s in sample:
                print(f'    例: p{s["page_no"]}#{s["line_idx"]} {(s.get("text") or "")[:60]}')

# annotations 表
print('\n=== annotations 表 ===')
annos = d.get('annotations', [])
acnt = Counter(a.get('form_type') for a in annos)
print(f'  总数: {len(annos)}, 分布: {dict(acnt)}')
# 检查 annotations 是否有 edition
edition_per_anno = Counter(a.get('edition') for a in annos)
print(f'  按 edition: {dict(edition_per_anno)}')
