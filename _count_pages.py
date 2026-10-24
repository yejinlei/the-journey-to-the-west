import re
from collections import defaultdict
with open('_bh_dump_61_80.txt', encoding='utf-8') as f:
    txt = f.read()
keys = re.findall(r'\[(\d+),(\d+)\]', txt)
print('all keys count:', len(keys))
d = defaultdict(list)
for p, l in keys:
    d[int(p)].append(int(l))
for p in sorted(d):
    print(f'{p}: {len(d[p])} -> {d[p]}')
print('total', sum(len(v) for v in d.values()))
