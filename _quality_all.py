"""全库翻译质量扫描：繁残留 + 长度比异常 + 空字段"""
import json, opencc
from collections import defaultdict

_T2S = opencc.OpenCC('t2s')

# 保护字表：合理保留的繁体/罕用字
PROTECTED = set('乾坤竅猻嬈卽攛蟄鎔剮嫗竈塚壘嬈甯瞭竇覓羣彆羣彙齣彆羣齣羣彙齣羣')

d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())
editions = sorted(set(l.get('edition') for l in d['lines'] if l.get('edition')))

print('=' * 72)
print('各版本翻译质量总览')
print('=' * 72)
print(f'{"版本":<22} {"总行":>6} {"main":>5} {"anno":>5} {"filled":>7} {"缺失":>4} {"高繁":>4} {"异常长度":>7}')
print('-' * 72)

summary = []
for ed in editions:
    lines = [l for l in d['lines'] if l.get('edition') == ed]
    total = len(lines)
    main = sum(1 for l in lines if l.get('form_type') == 'main')
    anno = sum(1 for l in lines if l.get('form_type') in ('commentary','annotation','pingshi'))
    other = total - main - anno
    filled = sum(1 for l in lines if l.get('text_zh'))
    missing = total - filled
    
    # 繁残留：>5%
    high_complex = 0
    # 长度比异常：len(text_zh) < 0.6 * len(text) 或 > 2.5 * len(text)
    abnormal_len = 0
    for l in lines:
        t = l.get('text') or ''
        z = l.get('text_zh') or ''
        if not t or not z:
            continue
        # 繁残留
        simp = _T2S.convert(z)
        diffs = [a for a, b in zip(z, simp) if a != b and a not in PROTECTED]
        if len(diffs) / max(len(z), 1) > 0.05:
            high_complex += 1
        # 长度比
        ratio = len(z) / max(len(t), 1)
        if ratio < 0.6 or ratio > 2.5:
            abnormal_len += 1
    
    summary.append((ed, total, main, anno, other, filled, missing, high_complex, abnormal_len))
    print(f'{ed:<22} {total:>6} {main:>5} {anno:>5} {other:>5} {filled:>7} {missing:>4} {high_complex:>4} {abnormal_len:>7}')

print()
print('=' * 72)
print('需关注的问题样本')
print('=' * 72)

for ed in editions:
    lines = [l for l in d['lines'] if l.get('edition') == ed]
    # 缺失 text_zh
    missing_zh = [l for l in lines if not l.get('text_zh')]
    # 繁残留高的样本
    high = []
    for l in lines:
        t = l.get('text') or ''
        z = l.get('text_zh') or ''
        if not t or not z: continue
        simp = _T2S.convert(z)
        diffs = [a for a, b in zip(z, simp) if a != b and a not in PROTECTED]
        if len(diffs) / max(len(z), 1) > 0.05:
            high.append((l['page_no'], l['line_idx'], l.get('form_type'), ''.join(set(diffs))[:12], len(diffs)/len(z)))
    if missing_zh or high:
        print(f'\n### {ed}')
        if missing_zh:
            print(f'  缺失 text_zh: {len(missing_zh)} 条')
            for l in missing_zh[:3]:
                print(f'    p{l["page_no"]}#{l["line_idx"]} {l.get("form_type")}: {(l.get("text") or "")[:60]}')
        if high:
            print(f'  高繁残留(>5%): {len(high)} 条')
            for p, i, ft, chars, r in high[:5]:
                print(f'    p{p}#{i} {ft} [{chars}] {r:.1%}')
