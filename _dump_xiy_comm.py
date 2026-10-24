# -*- coding: utf-8 -*-
"""输出到文件 - 详细查看 commentary"""
import json
from collections import Counter, defaultdict
from pathlib import Path

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))

out = []
# 每种 edition 每种长度统计
by_edition = defaultdict(lambda: Counter())
# 每种 edition 每种长度取一条样本
samples = defaultdict(dict)
# 每种 edition 未翻译行数
untranslated = defaultdict(list)

for l in d['lines']:
    if l.get('form_type') != 'commentary':
        continue
    ed = l['edition']
    t = l['text']
    by_edition[ed][len(t)] += 1
    if len(t) not in samples[ed]:
        samples[ed][len(t)] = t
    if not l.get('text_zh'):
        untranslated[ed].append((l['page_no'], l['line_idx'], t))

for ed in sorted(by_edition.keys()):
    out.append(f'=== {ed} ===')
    out.append(f'  len distribution: {dict(sorted(by_edition[ed].items()))}')
    out.append(f'  samples per len:')
    for ln in sorted(samples[ed].keys()):
        out.append(f'    len={ln}: {repr(samples[ed][ln][:100])}')
    out.append(f'  untranslated count: {len(untranslated[ed])}')
    if untranslated[ed]:
        out.append(f'  untranslated samples:')
        for s in untranslated[ed][:20]:
            out.append(f'    p{s[0]}i{s[1]}: {repr(s[2][:120])}')
    out.append('')

Path('_comm_report.txt').write_text('\n'.join(out), encoding='utf-8')
print('wrote')
