"""导出 xiyouji_zhuan 全部被截断的 main 行"""
import json
d = json.loads(open('docs/data/pages/read.json', 'r', encoding='utf-8').read())
lines = [l for l in d['lines'] if l.get('edition')=='xiyouji_zhuan' and l.get('form_type')=='main']
out = []
for l in lines:
    t = l.get('text') or ''
    z = l.get('text_zh') or ''
    if len(t) > 100 and len(z) < len(t)*0.7:
        out.append({'page_no': l['page_no'], 'line_idx': l['line_idx'], 'text': t, 'old_zh': z})
print(f'共 {len(out)} 行需要重译')
json.dump(out, open('_xyzhuan_trunc.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
