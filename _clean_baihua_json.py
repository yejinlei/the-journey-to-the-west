import json, re
from pathlib import Path
p = Path("_baihua_mapping.json")
raw = p.read_text(encoding="utf-8")
# 去掉最后一个 entry 结尾的多余逗号，再闭合 }
# 结构:  {  ...\n  "k": "v",\n}\n
# 需要变成 {  ...\n  "k": "v"\n}\n
lines = raw.splitlines()
# 找到最后一个非空非"}"的行，去掉其末尾的逗号
for i in range(len(lines)-1, -1, -1):
    if lines[i].strip() and lines[i].strip() != "}":
        if lines[i].rstrip().endswith(","):
            lines[i] = lines[i].rstrip()[:-1]
        break
new_raw = "\n".join(lines) + "\n"
p.write_text(new_raw, encoding="utf-8")
d = json.loads(new_raw)
print("OK entries:", len(d))
