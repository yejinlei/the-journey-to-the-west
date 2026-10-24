import json
d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())
print('=== xiyouji_zhuan 完整 144 行 text_zh 长度分布 ===')
lines = [l for l in d['lines'] if l.get('edition') == 'xiyouji_zhuan']
lens = sorted((len(l.get('text_zh') or ''), l['page_no'], l['line_idx']) for l in lines)
print('最短 5 行:')
for x in lens[:5]:
    print(f'  len={x[0]} p{x[1]}#{x[2]}')
print('最长 5 行:')
for x in lens[-5:]:
    print(f'  len={x[0]} p{x[1]}#{x[2]}')
print('平均:', sum(x[0] for x in lens) / len(lens))

print('\n=== 抽样 3 条比较原文 vs 白话 ===')
for l in lines[:2]:
    t = l.get('text') or ''
    z = l.get('text_zh') or ''
    print(f'--- p{l["page_no"]}#{l["line_idx"]} t={len(t)} z={len(z)} ---')
    print('原:', t[:300])
    print('白:', z[:300])
    print('白末:', z[-80:] if z else '')

print('\n=== xiyou_yuanzhi 完整 256 行 ===')
yyz = [l for l in d['lines'] if l.get('edition') == 'xiyou_yuanzhi']
for l in yyz:
    t = l.get('text') or ''
    z = l.get('text_zh') or ''
    if l['form_type'] == 'main' and len(t) > 50:
        print(f'--- p{l["page_no"]}#{l["line_idx"]} {l["form_type"]} t={len(t)} z={len(z)} ---')
        print('原:', t[:200])
        print('白:', z[:200])
        print('白末:', z[-80:] if z else '')
