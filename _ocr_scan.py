"""扫描全库 OCR 残余与代码污染"""
import json, re
from collections import defaultdict

d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())

# 各类可疑模式
PATTERNS = {
    'json_code': r'(notes\s*=|\{\{|\}\}|=>|\[object|undefined|NaN|null|None\b)',
    'pipe_english': r'[^ \u4e00-\u9fff]\|\s*\w+',  # | xxx 英文
    'script_tags': r'</?[a-zA-Z][^>]*>',
    'url': r'https?://',
    'double_pipe': r'\|\|',
    'stray_ascii_word': r'[\u4e00-\u9fff]\s+[a-z]{4,}\b',
    'comma_pipe_end': r'\|\s*[{}]',
}

# 只扫 text（原文）与 text_zh
fields = ['text', 'text_zh']

hits = defaultdict(list)  # pattern -> [(edition, page, line_idx, field, sample)]
edition_counts = defaultdict(lambda: defaultdict(int))

for l in d['lines']:
    ed = l.get('edition', '?')
    form = l.get('form_type', '?')
    page = l.get('page_no', 0)
    li = l.get('line_idx', 0)
    for f in fields:
        v = l.get(f) or ''
        if not v: continue
        for name, pat in PATTERNS.items():
            m = re.search(pat, v)
            if m:
                # 记录样本
                sample = v[max(0, m.start()-15):m.end()+15]
                hits[name].append((ed, form, page, li, f, sample, m.group(0)))
                edition_counts[ed][name] += 1

# 输出汇总
print('=' * 72)
print('OCR 残余扫描汇总（按模式 × 版本）')
print('=' * 72)
for pat, items in hits.items():
    print(f'\n--- [{pat}] 命中 {len(items)} 处 ---')
    by_ed = defaultdict(int)
    for x in items:
        by_ed[x[0]] += 1
    for ed, n in sorted(by_ed.items(), key=lambda kv: -kv[1]):
        print(f'  {ed}: {n}')
    # 样本
    print('  样本（最多 8 条）:')
    for x in items[:8]:
        ed, form, pg, li, fld, sample, mt = x
        print(f'    [{ed}/{form} p{pg}#{li} {fld}] "...{sample}..."')

# 特别找 'notes =' 这种被误当成正文的
print('\n' + '=' * 72)
print("特别关注: 含 'notes' 或 '}}' 的行")
print('=' * 72)
suspects = []
for l in d['lines']:
    for f in fields:
        v = l.get(f) or ''
        if 'notes' in v or '}}' in v or '{{' in v:
            suspects.append((l.get('edition'), l.get('form_type'), l.get('page_no'), l.get('line_idx'), f, v[:120]))
for s in suspects[:40]:
    print(f'  {s}')
print(f'\n共 {len(suspects)} 条疑似 OCR 代码污染')
