# -*- coding: utf-8 -*-
"""xu_xiyouji page 28-37 翻译（繁->简，保留术语，标准化引号）

从 _xxj_dump_28_37.txt 读回原文，
使用「繁->简 + 术语遮蔽 + 引号规范化」写入 read.json 的 text_zh。
"""
import json
import re
from pathlib import Path
import opencc

BASE = Path(__file__).resolve().parent.parent
DUMPS = [BASE / '_xxj_dump_28_37.txt']
READ_JSON = BASE / 'docs/data/pages/read.json'

# ---- 受保护的术语/字（传统形式保留，其它一律走 OpenCC 繁→简） ----
PROTECTED = [
    '乾',
    '坤',
    '竅',
]
# 去重 + 长词优先
PROTECTED = sorted(set(PROTECTED), key=lambda s: -len(s))


def mask_protected(s: str):
    mapping = {}
    idx = 0

    def repl(m):
        nonlocal idx
        key = f'\x00{idx}\x00'
        mapping[key] = m.group(0)
        idx += 1
        return key

    pattern = re.compile('|'.join(re.escape(t) for t in PROTECTED))
    return pattern.sub(repl, s), mapping


def unmask_protected(s: str, mapping: dict) -> str:
    for k, v in mapping.items():
        s = s.replace(k, v)
    return s


def norm_quotes(s: str) -> str:
    out = []
    stack = []
    outer_open = {'\u300c', '\u201c'}
    outer_close = {'\u300d', '\u201d'}
    inner_open = {'\u300e', '\u2018'}
    inner_close = {'\u300f', '\u2019'}
    for ch in s:
        if ch in outer_open:
            stack.append(ch)
            out.append("'")
        elif ch in inner_open:
            stack.append(ch)
            out.append('"')
        elif ch in outer_close:
            if stack:
                while stack:
                    top = stack.pop()
                    if top in outer_open:
                        break
            out.append("'")
        elif ch in inner_close:
            if stack:
                while stack:
                    top = stack.pop()
                    if top in inner_open:
                        break
            out.append('"')
        else:
            out.append(ch)
    return ''.join(out)


_T2S = opencc.OpenCC('t2s')


def to_zh(text: str) -> str:
    masked, mapping = mask_protected(text)
    simp = _T2S.convert(masked)
    simp = unmask_protected(simp, mapping)
    simp = norm_quotes(simp)
    return simp


def load_dump():
    out = []
    for dump in DUMPS:
        cur_key = None
        buf = []
        with dump.open(encoding='utf-8') as f:
            for raw in f:
                line = raw.rstrip('\n')
                m = re.match(r'\[(\d+),(\d+)\] === (\w+)', line)
                if m:
                    if cur_key is not None:
                        out.append((cur_key[0], cur_key[1], cur_key[2], ''.join(buf).rstrip('\n')))
                    cur_key = (int(m.group(1)), int(m.group(2)), m.group(3))
                    buf = []
                elif line == '---':
                    if cur_key is not None:
                        out.append((cur_key[0], cur_key[1], cur_key[2], ''.join(buf).rstrip('\n')))
                    cur_key = None
                    buf = []
                else:
                    if cur_key is not None:
                        buf.append(line + '\n')
        if cur_key is not None:
            out.append((cur_key[0], cur_key[1], cur_key[2], ''.join(buf).rstrip('\n')))
    return out


def main():
    data = json.loads(READ_JSON.read_text(encoding='utf-8'))
    rows = load_dump()

    by_key = {(l['page_no'], l['line_idx']): l for l in data['lines']
              if l.get('edition') == 'xu_xiyouji'}

    count = 0
    for page, lidx, form_type, text in rows:
        key = (page, lidx)
        row = by_key.get(key)
        if row is None:
            continue
        zh = to_zh(text)
        row['text_zh'] = zh
        count += 1

    READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'写入 {count} 行')


if __name__ == '__main':
    main()
