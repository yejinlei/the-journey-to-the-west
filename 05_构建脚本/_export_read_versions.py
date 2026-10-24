"""从 docs/data/pages/read.json 导出按版本拆分的 slim 数据到 06_Web前端/data/read/

- 只保留前端渲染需要的字段（行号、类型、原文、白话、评点标记）
- 按 edition 拆成独立 JSON，支持前端按需加载
- 生成 index.json 供前端发现可用版本
"""
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs', 'data', 'pages', 'read.json')
DST = os.path.join(ROOT, '06_Web前端', 'data', 'read')

def main():
    with open(SRC, encoding='utf-8') as f:
        d = json.load(f)
    os.makedirs(DST, exist_ok=True)
    # 清空旧文件
    for name in os.listdir(DST):
        if name.endswith('.json'):
            os.remove(os.path.join(DST, name))

    editions = [
        {'id': e['edition_id'], 'name': e['display_name'], 'pub': e.get('publisher', '')}
        for e in d['editions']
    ]

    index = {'editions': editions, 'versions': {}}

    for e in d['editions']:
        eid = e['edition_id']
        ed_lines = [l for l in d['lines'] if l['edition'] == eid]
        if not ed_lines:
            continue
        chs = sorted(
            [c for c in d['chapters'] if c['edition'] == eid],
            key=lambda c: c['first_page']
        )

        # 建立 page_no -> chapter 映射（取最大的 first_page <= page_no）
        def find_chapter(page_no):
            owner = None
            for c in chs:
                if c['first_page'] <= page_no:
                    owner = c
                else:
                    break
            return owner

        # 按 chapter 分组
        groups = defaultdict(list)
        for l in ed_lines:
            owner = find_chapter(l['page_no'])
            if owner is None:
                continue
            groups[owner['chapter_id']].append(l)

        chapters_out = []
        total_lines = 0
        for c in chs:
            lines = groups.get(c['chapter_id'], [])
            lines_out = []
            for l in lines:
                rec = {'i': l['line_idx'], 't': l['form_type'], 'x': l['text']}
                if l.get('text_zh'):
                    rec['z'] = l['text_zh']
                if l.get('is_commentary'):
                    rec['c'] = 1
                lines_out.append(rec)
            chapters_out.append({
                'l': c['chapter_label'],
                't': c.get('chapter_title', ''),
                'p': c['first_page'],
                'lines': lines_out
            })
            total_lines += len(lines_out)

        fname = f'{eid}.json'
        with open(os.path.join(DST, fname), 'w', encoding='utf-8') as f:
            json.dump(chapters_out, f, ensure_ascii=False, separators=(',', ':'))
        sz = os.path.getsize(os.path.join(DST, fname))
        index['versions'][eid] = {
            'file': fname,
            'name': e['display_name'],
            'pub': e.get('publisher', ''),
            'chapters': len(chapters_out),
            'lines': total_lines,
            'size_kb': round(sz / 1024, 1)
        }
        print(f'{eid}: {len(chapters_out)} ch, {total_lines} lines, {sz/1024:.0f}KB')

    with open(os.path.join(DST, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False)
    print(f'\nfiles written to {DST}')
    print(f'total: {sum(v["size_kb"] for v in index["versions"].values()):.0f}KB')

if __name__ == '__main__':
    main()
