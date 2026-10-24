"""补充分析：annotations 详情 + gubao verse/prose 拆分。"""
import json
from collections import Counter, defaultdict

d = json.load(open(r'f:\src\The-Journey-to-the-West\docs\data\pages\read.json', encoding='utf-8'))

# 1. annotations 按 edition / form_type 分布
ann = d['annotations']
print('=== annotations 按 edition ===')
by_e = Counter(a['edition'] for a in ann)
for e, c in by_e.most_common():
    print(f'  {e:22s} {c}')
print('=== annotations 按 form_type ===')
for ft, c in Counter(a['form_type'] for a in ann).most_common():
    print(f'  {ft:12s} {c}')
print('=== annotations 样本 3 条 ===')
for a in ann[:3]:
    print(json.dumps(a, ensure_ascii=False)[:200])
# 找 xinke_pingbi 的一些 annotation
print('=== xinke_pingbi annotations 样例 ===')
for a in ann:
    if a['edition'] == 'xinke_pingbi':
        print(json.dumps(a, ensure_ascii=False)[:200])
        break

# 2. gubao verse vs prose 挂载
gb = [l for l in d['lines'] if l['edition'] == 'gubao']
print()
print('=== gubao form_type 与 text_zh 长度对比 ===')
by_form = defaultdict(list)
for l in gb:
    by_form[l['form_type']].append(len(l.get('text_zh','') or ''))
for ft, ls in by_form.items():
    avg = sum(ls)/len(ls)
    print(f'  {ft:8s} 数={len(ls):4d}  avg_zh_len={avg:.1f}  min={min(ls)}  max={max(ls)}')

# 3. 检查 gubao verse 行是否 text_zh == text（是否只保留繁体原文）
print()
print('=== gubao verse 行 text_zh 是否与 text 一致 ===')
verse = [l for l in gb if l['form_type'] == 'verse']
same = sum(1 for l in verse if l.get('text_zh','') == l.get('text',''))
print(f'  verse 总 {len(verse)}，text_zh==text: {same}')

# 4. gubao main 中有多少行"内嵌韵文段"（text 内含 :xxx 分隔）
main = [l for l in gb if l['form_type'] == 'main']
embedded = 0
embedded_zh_has_embedded = 0
for l in main:
    if ' :' in l['text'] or ' :' in l.get('text_zh',''):
        embedded += 1
print(f'  main 总 {len(main)}，text 含 " : " 内嵌韵文段: {embedded}')

# 5. 每回行数分布（gubao）
print()
print('=== gubao 每回行数分布（page_no） ===')
by_p = Counter(l['page_no'] for l in gb)
counts = list(by_p.values())
print(f'  回数={len(counts)}  每回平均={sum(counts)/len(counts):.1f}  min={min(counts)}  max={max(counts)}')

# 6. 检查 gubao prose 译文的字符比例（zh_len / text_len），看是否有异常
print()
print('=== gubao prose 翻译字符比例 ===')
ratios = []
for l in gb:
    if l['form_type'] != 'main':
        continue
    t = l['text']
    z = l.get('text_zh','') or ''
    if t and z:
        ratios.append(len(z)/len(t))
ratios.sort()
n = len(ratios)
print(f'  样本={n}  中位={ratios[n//2]:.2f}  p10={ratios[n//10]:.2f}  p90={ratios[9*n//10]:.2f}')
# 找比例异常小的（疑似漏译）
print('  比例 < 0.4 的行数:', sum(1 for r in ratios if r < 0.4))
print('  比例 > 1.5 的行数:', sum(1 for r in ratios if r > 1.5))

# 7. 检查有没有 text_zh 是空的
empty_zh = [(l['page_no'], l['line_idx']) for l in gb if not l.get('text_zh')]
print()
print(f'=== gubao text_zh 为空的行数: {len(empty_zh)} ===')
if empty_zh:
    print('样例:', empty_zh[:5])
