# -*- coding: utf-8 -*-
"""baihui_xiangzhu page 81-100 翻译

繁→简 + 术语遮蔽 + 引号规范化流程：
- OpenCC t2s 做主体繁简转换
- PROTECTED 仅包含：(1) OpenCC 会误转的字（乾→干）；
                     (2) 用户明确要求保留原名的特殊称谓
- 术语（金刚、法华、还丹、参同、阴符、金箍棒、九齿耙…）走常规简化
- 外层「」→ U+0027 单引号 '...'；内层『』→ U+0022 双引号 "..."
- 保留所有括号、古籍引注、特殊标记（-{丑}- 等）

输入：_bh_dump_81_100.txt（由 _dump_baihui.py 81-100 生成）
输出：docs/data/pages/read.json 中 baihui_xiangzhu 对应 page 的 text_zh 字段
"""
import json
import re
from pathlib import Path
import opencc

BASE = Path(__file__).resolve().parent.parent
DUMP = BASE / '_bh_dump_81_100.txt'
READ_JSON = BASE / 'docs/data/pages/read.json'

# ---- 需要遮蔽保护的字/词 ----
# 只列 OpenCC 会误转或用户明确要保留的项
PROTECTED = [
    '乾',           # OpenCC 会误转成 干
    '金縵棒',        # OpenCC 会误转成 金缦棒；用户术语列表写的是"金箍棒"，
                    # 但原文作"金縵棒"，保留原字形
]
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
    """「」→ ' ；『』→ "（全角双/单引号也一并归一）。"""
    out = []
    stack = []
    outer_open = {'\u300c', '\u201c'}   # 「  "
    outer_close = {'\u300d', '\u201d'}  # 」  "
    inner_open = {'\u300e', '\u2018'}   # 『  '
    inner_close = {'\u300f', '\u2019'}  # 』  '
    for ch in s:
        if ch in outer_open:
            stack.append(ch)
            out.append("'")
        elif ch in inner_open:
            stack.append(ch)
            out.append('"')
        elif ch in outer_close:
            while stack and stack[-1] not in outer_open:
                stack.pop()
            if stack:
                stack.pop()
            out.append("'")
        elif ch in inner_close:
            while stack and stack[-1] not in inner_open:
                stack.pop()
            if stack:
                stack.pop()
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
    """返回 [(page, line_idx, form_type, text), ...]"""
    out = []
    cur_key = None
    buf = []
    with DUMP.open(encoding='utf-8') as f:
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

    by_key = {}
    for l in data['lines']:
        if l.get('edition') != 'baihui_xiangzhu' or l.get('form_type') not in ('main', 'verse'):
            continue
        if not (81 <= l['page_no'] <= 100):
            continue
        by_key[(l['page_no'], l['line_idx'])] = l

    count = 0
    missing = []
    for page, lidx, form_type, text in rows:
        if (page, lidx) not in by_key:
            missing.append((page, lidx))
            continue
        by_key[(page, lidx)]['text_zh'] = to_zh(text)
        count += 1

    if missing:
        print(f'未在 read.json 中找到: {missing}')

    READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'写入 {count} 行')


if __name__ == '__main__':
    main()
