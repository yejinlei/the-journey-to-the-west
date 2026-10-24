"""xiyouji_zhuan 24 行截断修复

策略：西游记原文本身就是白话小说，不需要真白话改写。
      只需 OpenCC t2s 完整转简繁 + 全角引号规范化 + 保留全部内容。

引号规则：外层「」→ '...' (U+0027)，内层『』→ "..." (U+0022)
        原旧白话也用 ' 与 "，与全局规则一致
"""
import json, opencc
from pathlib import Path

T2S = opencc.OpenCC('t2s')
SRC = Path('docs/data/pages/read.json')
d = json.loads(SRC.read_text(encoding='utf-8'))

def normalize_quotes(s):
    """把「」→'  『』→"  同时避免嵌套冲突"""
    # 「」最外层；『』内层
    # 策略：直接一一映射
    out = []
    # 记录状态：是否已在「」内
    in_outer = False
    in_inner = False
    for ch in s:
        if ch == '「':
            out.append("'"); in_outer = True
        elif ch == '」':
            out.append("'"); in_outer = False
        elif ch == '『':
            out.append('"'); in_inner = True
        elif ch == '』':
            out.append('"'); in_inner = False
        elif ch == '"':
            # 半角双引号保留
            out.append(ch)
        elif ch == "'":
            out.append(ch)
        else:
            out.append(ch)
    return ''.join(out)

# 只处理被截断的 24 行
trunc = json.loads(Path('_xyzhuan_trunc.json').read_text(encoding='utf-8'))
updated = 0
for item in trunc:
    pg, li = item['page_no'], item['line_idx']
    row = None
    for l in d['lines']:
        if l.get('edition') == 'xiyouji_zhuan' and l['page_no'] == pg and l['line_idx'] == li:
            row = l
            break
    if not row:
        print(f'  未找到 p{pg}#{li}')
        continue
    raw = row.get('text') or ''
    simp = T2S.convert(raw)
    final = normalize_quotes(simp)
    row['text_zh'] = final
    updated += 1
    print(f'  p{pg}#{li}: 原文{len(raw)}字 → 新白话{len(final)}字')

print(f'\n已修复 {updated} 行')

# 罕用字清理
HAN_CHARS = {'袞': '滚', '徵': '征', '長': '长', '鼕': '冬', '孃': '娘', '箇': '个'}
for l in d['lines']:
    for fld in ('text', 'text_zh'):
        v = l.get(fld) or ''
        if not v: continue
        new = v
        for k, val in HAN_CHARS.items():
            if k in new:
                new = new.replace(k, val)
        if new != v:
            l[fld] = new

SRC.write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print('已写回 read.json')
