import re, sys
p = r'f:\src\The-Journey-to-the-West\docs\lib\duckdb\duckdb.bundle.js'
with open(p, 'r', encoding='utf-8') as f:
    b = f.read()
hits = set(re.findall(r'instantiateWith[A-Za-z]*', b))
print('API methods:', sorted(hits))
# 找 AsyncDuckDB class 的方法定义
for m in re.finditer(r'AsyncDuckDB', b):
    s = max(0, m.start()-20); e = min(len(b), m.end()+80)
    print('...', b[s:e].replace('\n',' '), '...')
