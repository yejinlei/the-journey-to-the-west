import json, opencc
_T2S = opencc.OpenCC('t2s')
d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())
all_lines = [l for l in d['lines'] if l.get('edition') == 'gubao']
total = len(all_lines)
filled = [l for l in all_lines if l.get('text_zh')]
missing = total - len(filled)
high = 0
high_samples = []
for l in filled:
    zh = l['text_zh']
    simp = _T2S.convert(zh)
    diffs = [a for a, b in zip(zh, simp) if a != b]
    ratio = len(diffs) / max(len(zh), 1)
    if ratio > 0.05:
        high += 1
        if len(high_samples) < 5:
            high_samples.append((l['page_no'], l['line_idx'], ratio, ''.join(set(diffs))[:15]))
print(f'gubao total lines: {total}')
print(f'filled: {len(filled)}  missing: {missing}  coverage: {100*len(filled)/total:.1f}%')
print(f'高繁残留(>5%): {high}')
if high_samples:
    print('高繁样本:')
    for s in high_samples:
        print(' ', s)
