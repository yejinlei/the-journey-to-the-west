# -*- coding: utf-8 -*-
"""xinke_pingbi 的 title / poem 短文本直接繁简转换（不做白话改写）。
- title: 回目标题/版本名，直接转换
- poem: 诗句，逐句转换即可，不做改写
"""
import json
import re
from pathlib import Path
import opencc

BASE = Path(__file__).resolve().parent.parent
READ_JSON = BASE / 'docs/data/pages/read.json'

PROTECTED = sorted(set(['乾', '坤', '竅']), key=lambda s: -len(s))

def mask_protected(s):
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

def unmask_protected(s, mapping):
    for k, v in mapping.items():
        s = s.replace(k, v)
    return s

def norm_quotes(s):
    out, stack = [], []
    outer_open = {'\u300c', '\u201c'}
    outer_close = {'\u300d', '\u201d'}
    inner_open = {'\u300e', '\u2018'}
    inner_close = {'\u300f', '\u2019'}
    for ch in s:
        if ch in outer_open:
            stack.append(ch); out.append("'")
        elif ch in inner_open:
            stack.append(ch); out.append('"')
        elif ch in outer_close:
            while stack:
                if stack.pop() in outer_open: break
            out.append("'")
        elif ch in inner_close:
            while stack:
                if stack.pop() in inner_open: break
            out.append('"')
        else:
            out.append(ch)
    return ''.join(out)

_T2S = opencc.OpenCC('t2s')
def to_zh(text):
    m, mp = mask_protected(text)
    s = _T2S.convert(m)
    s = unmask_protected(s, mp)
    s = norm_quotes(s)
    return s

data = json.loads(READ_JSON.read_text(encoding='utf-8'))
count = 0
for l in data['lines']:
    if l.get('edition') != 'xinke_pingbi':
        continue
    if l.get('form_type') not in ('title', 'poem'):
        continue
    if l.get('text_zh'):
        continue
    l['text_zh'] = to_zh(l['text'])
    count += 1

READ_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'写入 title+poem: {count} 条')
