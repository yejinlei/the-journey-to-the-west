"""诊断 xiyouji_zhuan 错乱"""
import json
d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())
lines = [l for l in d['lines'] if l.get('edition') == 'xiyouji_zhuan']
print(f'共 {len(lines)} 行')
# 每行：page, line_idx, form_type, 原文头 40, 白话头 40
for l in lines:
    t = l.get('text') or ''
    z = l.get('text_zh') or ''
    print(f'p{l["page_no"]:>3}#{l["line_idx"]:>2} {l.get("form_type"):>7}  原文[{len(t):>4}]: {t[:40]}')
    print(f'        白话[{len(z):>4}]: {z[:40]}')
    print()
