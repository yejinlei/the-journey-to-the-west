import json
d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())
lines = [l for l in d['lines'] if l.get('edition') == 'xiyou_bu']
abn = []
for l in lines:
    t = l.get('text') or ''
    z = l.get('text_zh') or ''
    if not t or not z: continue
    r = len(z) / max(len(t), 1)
    if r < 0.6 or r > 2.5:
        abn.append((l['page_no'], l['line_idx'], l.get('form_type'), len(t), len(z), round(r,2), t[:60], z[:60]))
print(f'xiyou_bu 长度比异常: {len(abn)}')
for a in abn:
    print(f"p{a[0]}#{a[1]} {a[2]} 原{a[3]}字/白{a[4]}字 比{a[5]}")
    print(f'  原: {a[6]}')
    print(f'  白: {a[7]}')
