import re, json
lines = open(r"f:\src\The-Journey-to-the-West\_xkb_merged.txt", encoding="utf-8").read().split("\n")
for i, line in enumerate(lines):
    m = re.match(r"## (p\d+)$", line.strip())
    if m and m.group(1) == "p50":
        width_str = lines[i+2].replace("LINE_WIDTHS", "").strip()
        widths = json.loads(width_str)
        print(f"width_str: {width_str}")
        print(f"widths length: {len(widths)}")
        print(f"widths: {widths}")
        print(f"manual sum: {sum(widths)}")
        # Verify: count each value
        from collections import Counter
        print(f"counter: {Counter(widths)}")
        print(f"expected: 14*22 + 4*21 + 3 + 3*22 = {14*22 + 4*21 + 3 + 3*22}")
        src = lines[i+4]
        print(f"src_len: {len(src)}")
