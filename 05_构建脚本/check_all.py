import re

with open('_batch_91_100.md', encoding='utf-8') as f:
    content = f.read()

entry_re = re.compile(
    r"### \[p(\d+)L(\d+)\] form=(\w+)\s*\n\s*\n\*\*原文\*\*：(.*?)\s*\n\s*\n\*\*译文\*\*：(.*?)\s*\n",
    re.DOTALL,
)

targets = {
    (91, 3): ['金灯桥', '月金'],
    (91, 11): ['不成问', '問他', '問他'],
    (91, 12): ['妖异', '妖異', '三個', '三个'],
    (93, 4): ['卻也就算讓開', '却也就算讓', '讓開些路', '让开些路'],
    (96, 10): ['却陪', '卻陪'],
    (97, 2): ['谂得', '吓得'],
    (97, 3): ['若是老實', '若是老实', '若是老實頭'],
    (98, 9): ['卻入', '却入'],
    (98, 11): ['不曾堤防', '不曾提防'],
    (99, 3): ['屣波', '履波'],
    (99, 4): ['谂得那三藏'],
    (100, 4): ['扭过来'],
    (100, 6): ['無一無', '無一不', '無一无'],
    (100, 12): ['不可輕', '不可轻', '轻褫', '輕褫'],
    (100, 14): ['对如来'],
    (100, 15): ['涨起', '长起'],
}

for m in entry_re.finditer(content):
    page, line = int(m.group(1)), int(m.group(2))
    if (page, line) not in targets: continue
    trans = m.group(5)
    print(f"\n=== [p{page}L{line}] ===")
    for kw in targets[(page, line)]:
        pos = trans.find(kw)
        if pos >= 0:
            excerpt = trans[max(0,pos-3):pos+len(kw)+5]
            print(f"  KW '{kw}' at {pos}: {excerpt!r}")
            print(f"    hex: {' '.join(f'U+{ord(x):04X}' for x in excerpt)}")
