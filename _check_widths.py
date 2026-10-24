import re
lines = open(r"f:\src\The-Journey-to-the-West\_xkb_merged.txt", encoding="utf-8").read().split("\n")
for i, line in enumerate(lines):
    if re.match(r"## p(49|50|51|53|54|57|58|59|60|61)\b", line):
        page = re.search(r"p(\d+)", line).group(1)
        # next 3 lines are LINE_COUNT, LINE_WIDTHS, ---
        widths = eval(lines[i+2].replace("LINE_WIDTHS ", "").strip())
        src = lines[i+3+1] if False else None
        # source is 3 lines down after header
        src_idx = i + 4  # pN / LINE_COUNT / LINE_WIDTHS / --- / source
        src_text = lines[src_idx] if src_idx < len(lines) else ""
        print(f"p{page}: count_line={lines[i+1]}, widths_sum={sum(widths)}, widths_len={len(widths)}, src_len={len(src_text)}")
