import re

with open('_batch_91_100.md', encoding='utf-8') as f:
    content = f.read()

entry_re = re.compile(
    r"### \[p(\d+)L(\d+)\] form=(\w+)\s*\n\s*\n\*\*原文\*\*：(.*?)\s*\n\s*\n\*\*译文\*\*：(.*?)\s*\n",
    re.DOTALL,
)

# For each candidate, find specific keyword and dump exact context with hex
searches = {
    (91, 11): ['成問', '成问', '姓名'],
    (91, 12): ['三個', '三个', '妖异', '妖異', '妖精'],
    (93, 4):  ['讓', '让', '兒', '儿', '兒'],
    (97, 3):  ['若是', '老實', '老實頭', '老實頭兒', '實頭', '頭兒'],
    (98, 9):  ['卻入', '却入'],
    (98, 11): ['不曾', '堤防', '提防'],
    (100, 6): ['無一無', '無一不', '無一无', '無一'],
}

for m in entry_re.finditer(content):
    page, line = int(m.group(1)), int(m.group(2))
    if (page, line) not in searches: continue
    trans = m.group(5)
    print(f"\n=== [p{page}L{line}] ===")
    for kw in searches[(page, line)]:
        for mm in re.finditer(re.escape(kw), trans):
            pos = mm.start()
            excerpt = trans[max(0,pos-2):pos+len(kw)+3]
            print(f"  KW '{kw}' at {pos}: {excerpt!r}")
            print(f"    hex: {' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
