"""sync_web_data.py —— 将 04_knowledge_data 目录的 manifest.json 与 Parquet 同步到 06_Web前端/data/"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / '04_knowledge_data'
DST = ROOT / '06_Web前端' / 'data'

DST.mkdir(parents=True, exist_ok=True)

# 1) manifest.json
shutil.copy2(SRC / 'manifest.json', DST / 'manifest.json')
print(f'[sync] manifest.json -> {DST.name}/manifest.json')

# 2) 所有 .parquet 表
n = 0
for p in SRC.glob('*.parquet'):
    shutil.copy2(p, DST / p.name)
    n += 1
print(f'[sync] {n} parquet 表已同步')
print(f'[sync] 完成，前端可从 /data/manifest.json 加载')
