import json
b1 = json.load(open('_xkb_batch1.json', encoding='utf-8'))
print('batch1 pages:', [x['page'] for x in b1])
print('total lines:', sum(len(x['widths']) for x in b1))
for x in b1:
    ok = sum(x['widths']) == len(x['text_zh'])
    print(f"p{x['page']}: widths_len={len(x['widths'])}, sum={sum(x['widths'])}, len={len(x['text_zh'])}, ok={ok}")
