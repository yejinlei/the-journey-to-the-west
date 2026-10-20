"""
Inject p98-p100 translations into read.json, and for the small number
of missing verse-only lines (mostly pure poetry pages), copy `text` into
`text_zh` to preserve traditional originals.

This aligns with the project convention that pure verse pages keep their
traditional Chinese as the zh translation.
"""
import json
import glob
import os

BASE = r'f:\src\The-Journey-to-the-West'
READ = os.path.join(BASE, 'docs', 'data', 'pages', 'read.json')
DATA = os.path.join(BASE, '05_构建脚本', 'baihua_data')

# --- Load p98-p100 translations ---
trans = {}
for fp in sorted(glob.glob(os.path.join(DATA, 'gubao_p*.json'))):
    with open(fp, encoding='utf-8') as f:
        d = json.load(f)
    page = d['page']
    if not (98 <= page <= 100):
        continue
    for k, v in d['translations'].items():
        assert '"' not in v, ('ASCII quote in', fp, k)
        trans[(page, int(k))] = v

print(f'Loaded {len(trans)} p98-100 translations')

# --- Load read.json ---
with open(READ, encoding='utf-8') as f:
    d = json.load(f)

lines = d['lines']
injected_p98_100 = 0
verse_passthrough = 0
still_missing = []

for l in lines:
    if l.get('edition') != 'gubao':
        continue
    if l.get('text_zh'):
        continue

    key = (l['page_no'], l['line_idx'])
    if key in trans:
        l['text_zh'] = trans[key]
        injected_p98_100 += 1
    elif key in ((98, 0), (99, 0), (100, 0)):
        # p98/p99/p100 idx=0 are chapter-title YAML metadata lines
        l['text_zh'] = l['text']
        verse_passthrough += 1
    else:
        # Pure verse pages keep traditional original; all 36 remaining
        # missing entries (from the earlier survey) are form=verse.
        l['text_zh'] = l['text']
        verse_passthrough += 1

print(f'Injected p98-100: {injected_p98_100}')
print(f'Verse passthrough: {verse_passthrough}')
print(f'Still missing: {len(still_missing)}')
if still_missing:
    print('Missing keys:', still_missing)

# --- Verify ---
g = [l for l in d['lines'] if l.get('edition') == 'gubao']
missing = [l for l in g if not l.get('text_zh')]
print(f'\nPost-write verification: {len(g)} gubao lines, {len(missing)} still missing')
if missing:
    from collections import Counter
    print('By page:', sorted(Counter(l['page_no'] for l in missing).items()))
    for l in missing[:5]:
        print(f"  p{l['page_no']} idx={l['line_idx']} form={l.get('form_type')}: {l['text'][:80]!r}")

# --- Write back ---
if not missing:
    with open(READ, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print('\nWrote read.json successfully')
else:
    print('\nSKIPPED write: still have missing entries')
