"""直接看前端 gubao.json 的原文 bytes，找 notes 位置"""
from pathlib import Path
import json, re

p = Path('06_Web前端/data/read/gubao.json')
raw = p.read_text(encoding='utf-8')
print(f"文件大小: {len(raw)} bytes")

# 找 notes
for m in re.finditer(r'notes', raw):
    s = max(0, m.start() - 100)
    e = min(len(raw), m.end() + 100)
    print(f"  offset={m.start()}: ...{raw[s:e]}...")

# 找 }}
hits = list(re.finditer(r'\}\}', raw))
print(f"\n}} 出现次数: {len(hits)}")
for m in hits[:5]:
    s = max(0, m.start() - 100)
    e = min(len(raw), m.end() + 100)
    print(f"  offset={m.start()}: ...{raw[s:e]}...")

# 找尽三三行满道归根
for m in re.finditer(r'尽三三行满道归根', raw):
    s = max(0, m.start() - 80)
    e = min(len(raw), m.end() + 200)
    print(f"\n尽三三行@{m.start()}: ...{raw[s:e]}...")
