import re

with open('_batch_91_100.md', encoding='utf-8') as f:
    content = f.read()

entry_re = re.compile(
    r"### \[p(\d+)L(\d+)\] form=(\w+)\s*\n\s*\n\*\*原文\*\*：(.*?)\s*\n\s*\n\*\*译文\*\*：(.*?)\s*\n",
    re.DOTALL,
)

# p93L4: 算 duplicate
for m in entry_re.finditer(content):
    page, line = int(m.group(1)), int(m.group(2))
    if page == 93 and line == 4:
        orig = m.group(4)
        trans = m.group(5)
        print("=== p93L4 ===")
        for mm in re.finditer(r'算', trans):
            pos = mm.start()
            excerpt = trans[max(0,pos-5):pos+5]
            print(f"  算 at {pos}: {excerpt!r}  hex={' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
        for mm in re.finditer(r'算', orig):
            pos = mm.start()
            excerpt = orig[max(0,pos-5):pos+5]
            print(f"  ORIG 算 at {pos}: {excerpt!r}  hex={' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
        break

for m in entry_re.finditer(content):
    page, line = int(m.group(1)), int(m.group(2))
    if page == 98 and line == 9:
        orig = m.group(4)
        trans = m.group(5)
        print("\n=== p98L9 ===")
        for kw in ['却入', '卻入', '入宝', '入寶']:
            pos = trans.find(kw)
            if pos >= 0:
                excerpt = trans[max(0,pos-4):pos+len(kw)+4]
                print(f"  TRANS '{kw}' at {pos}: {excerpt!r}  hex={' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
            pos = orig.find(kw)
            if pos >= 0:
                excerpt = orig[max(0,pos-4):pos+len(kw)+4]
                print(f"  ORIG '{kw}' at {pos}: {excerpt!r}  hex={' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
        # Search for 却 or 卻
        for mm in re.finditer(r'[却卻]', trans):
            pos = mm.start()
            excerpt = trans[max(0,pos-3):pos+3]
            print(f"  '{mm.group(0)}' at {pos}: {excerpt!r}")
        break

for m in entry_re.finditer(content):
    page, line = int(m.group(1)), int(m.group(2))
    if page == 100 and line == 6:
        orig = m.group(4)
        trans = m.group(5)
        print("\n=== p100L6 ===")
        for kw in ['无一', '無一']:
            pos = trans.find(kw)
            if pos >= 0:
                excerpt = trans[max(0,pos-4):pos+len(kw)+4]
                print(f"  TRANS '{kw}' at {pos}: {excerpt!r}  hex={' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
            pos = orig.find(kw)
            if pos >= 0:
                excerpt = orig[max(0,pos-4):pos+len(kw)+4]
                print(f"  ORIG '{kw}' at {pos}: {excerpt!r}  hex={' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
        break
