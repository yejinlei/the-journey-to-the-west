import json
b1 = json.load(open('_xkb_batch1.json', encoding='utf-8'))
for x in b1[:3]:
    print(f"=== p{x['page']} ===")
    print(f"widths: {x['widths']}")
    print(f"sum: {sum(x['widths'])}, len: {len(x['text_zh'])}")
    print(f"text: {x['text_zh'][:200]}")
    print()
