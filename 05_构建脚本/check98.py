import re

with open('_batch_91_100.md', encoding='utf-8') as f:
    content = f.read()

entry_re = re.compile(
    r"### \[p(\d+)L(\d+)\] form=(\w+)\s*\n\s*\n\*\*原文\*\*：(.*?)\s*\n\s*\n\*\*译文\*\*：(.*?)\s*\n",
    re.DOTALL,
)

for m in entry_re.finditer(content):
    page, line = int(m.group(1)), int(m.group(2))
    if page == 98 and line in [9, 11]:
        trans = m.group(5)
        print(f"\n=== p{page}L{line} ===")
        # find 入宝 or 宝阁
        for mm in re.finditer(r'(卻|却)入(寶|宝)(閣|阁)', trans):
            pos = mm.start()
            excerpt = trans[max(0,pos-4):pos+len(mm.group(0))+4]
            print(f"  found: {excerpt!r}")
            print(f"    hex: {' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
        # also 未曾堤 or 未曾提
        for mm in re.finditer(r'未曾(堤|提)防', trans):
            pos = mm.start()
            excerpt = trans[max(0,pos-4):pos+len(mm.group(0))+4]
            print(f"  found: {excerpt!r}")
            print(f"    hex: {' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
        # Also for 却入, might just be at end
        if '却入' not in trans and '卻入' not in trans:
            # Try simpler
            print(f"  TRANS length: {len(trans)}")
            for kw in ['宝阁', '寶閣', '寶阁', '寶閣', '入宝', '入寶', '卻', '却']:
                pos = trans.find(kw)
                if pos >= 0:
                    ex = trans[max(0,pos-2):pos+len(kw)+3]
                    print(f"  '{kw}' at {pos}: {ex!r}  hex={' '.join(f'U+{ord(x):04X}' for x in ex)}")
