import re, json
lines = open(r"f:\src\The-Journey-to-the-West\_xkb_merged.txt", encoding="utf-8").read().split("\n")
for i, line in enumerate(lines):
    m = re.match(r"## (p\d+)$", line.strip())
    if m and m.group(1) in ("p49","p50","p51","p53","p54","p57","p58","p59","p60","p61"):
        page = m.group(1)
        width_str = lines[i+2].replace("LINE_WIDTHS", "").strip()
        widths = json.loads(width_str)
        src = lines[i+4]
        print(f"{page}: widths_list={widths} sum={sum(widths)} src_len={len(src)}")
