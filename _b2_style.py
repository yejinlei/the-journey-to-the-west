import json
b1 = json.load(open('_xkb_batch1.json', encoding='utf-8'))
# Print full text for a few pages for style reference
for x in b1:
    if x['page'] in [4, 17, 18]:
        print(f"=== p{x['page']} len={len(x['text_zh'])} ===")
        print(x['text_zh'])
        print()
