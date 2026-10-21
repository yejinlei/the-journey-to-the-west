"""
应用精校修改到 read.json。

patch 文件格式（UTF-8 JSON）：
{
  "batch": "p1-10",
  "changes": [
    {"page": 1, "line": 5, "text_zh": "...修正后的译文..."},
    ...
  ]
}

用法：
    py apply_patch.py --patch _patch_01.json
"""
import argparse
import json

READ = r'f:\src\The-Journey-to-the-West\docs\data\pages\read.json'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--patch', required=True)
    args = ap.parse_args()

    patch = json.load(open(args.patch, encoding='utf-8'))
    d = json.load(open(READ, encoding='utf-8'))

    # 建立 (page, line) -> record 索引
    idx = {}
    for l in d['lines']:
        if l.get('edition') == 'gubao':
            idx[(l['page_no'], l['line_idx'])] = l

    applied = 0
    not_found = 0
    has_quote = 0
    for c in patch['changes']:
        key = (c['page'], c['line'])
        if key not in idx:
            print(f'NOT FOUND: {key}')
            not_found += 1
            continue
        new_zh = c['text_zh']
        if '"' in new_zh:
            print(f'ASCII QUOTE in {key}: {new_zh[:50]!r}')
            has_quote += 1
        old_zh = idx[key].get('text_zh', '')
        idx[key]['text_zh'] = new_zh
        if old_zh != new_zh:
            applied += 1
        else:
            pass  # 无变化

    # 写回
    with open(READ, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f'Batch: {patch.get("batch", "?")}')
    print(f'Total changes: {len(patch["changes"])}')
    print(f'Applied (differ from old): {applied}')
    print(f'Not found: {not_found}')
    print(f'ASCII quote warnings: {has_quote}')

if __name__ == '__main__':
    main()
