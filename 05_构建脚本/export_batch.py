"""
导出指定页范围的古本原文+译文对照，供人工精校。
用法：
    py export_batch.py --range 1-10
    py export_batch.py --range 11-20 --out _batch_02.md

输出：Markdown 文件，每行含：
  [p1L5] 原文：...
        译文：...
"""
import argparse
import json

READ = r'f:\src\The-Journey-to-the-West\docs\data\pages\read.json'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--range', required=True, help='页范围，如 1-10')
    ap.add_argument('--out', help='输出文件路径')
    args = ap.parse_args()

    a, b = [int(x) for x in args.range.split('-')]
    out_path = args.out or f'_batch_{a:02d}_{b:02d}.md'

    d = json.load(open(READ, encoding='utf-8'))
    g = [l for l in d['lines'] if l.get('edition') == 'gubao' and a <= l['page_no'] <= b]

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'# 精校批次 p{a}-p{b}，共 {len(g)} 行\n\n')
        f.write(f'范围：第 {a} 页至第 {b} 页\n\n')
        f.write('---\n\n')
        for l in g:
            f.write(f"### [p{l['page_no']}L{l['line_idx']}] form={l.get('form_type')}\n\n")
            f.write(f"**原文**：{l['text']}\n\n")
            f.write(f"**译文**：{l.get('text_zh', '')}\n\n")
            f.write('---\n\n')

    print(f'Exported {len(g)} lines to {out_path}')

if __name__ == '__main__':
    main()
