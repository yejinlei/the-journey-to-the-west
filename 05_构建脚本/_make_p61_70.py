"""基于当前 read.json 的 text_zh，做字词级精确替换。避免整段重写导致的幻觉。"""
import json
import copy

READ = r'f:\src\The-Journey-to-the-West\docs\data\pages\read.json'
d = json.load(open(READ, encoding='utf-8'))

# 精校项：(page, line, old_substring, new_substring, reason)
# old_substring 必须唯一出现在 text_zh 里，否则报错不修改
CORRECTIONS = [
    (62, 16, "有德", "有疾", "语义反转：原文'有疾'指唐太宗患病，故选高僧取经"),
    (64, 5,  "萝菔", "萝蓏", "错字：原文'蘿蓏'为蔓藤类，与'葛藤'呼应；'菔'是萝卜"),
    (66, 2,  "龙、蛇、龟模样的人", "龙、蛇、龟相", "衍字：原文仅'龍蛇龜相'，译文多加'模样的人'"),
]

# 构建索引
lines_by_key = {}
for l in d['lines']:
    if l['edition'] == 'gubao':
        lines_by_key[(l['page_no'], l['line_idx'])] = l

changes = []
skipped = []

for page, line, old, new, reason in CORRECTIONS:
    key = (page, line)
    if key not in lines_by_key:
        skipped.append((key, "行不存在"))
        continue
    entry = lines_by_key[key]
    zh = entry.get('text_zh', '')
    cnt = zh.count(old)
    if cnt == 0:
        skipped.append((key, f"'{old}' 未在 text_zh 中找到"))
        continue
    if cnt > 1:
        skipped.append((key, f"'{old}' 出现 {cnt} 次，非唯一，跳过"))
        continue
    new_zh = zh.replace(old, new)
    changes.append({
        "page": page,
        "line": line,
        "text_zh": new_zh,
    })
    print(f"✓ p{page}L{line}: '{old}' → '{new}'  ({reason})")

for s in skipped:
    print(f"✗ p{s[0][0]}L{s[0][1]}: {s[1]}")

out = {"batch": "p61_70", "changes": changes}
with open(r'f:\src\The-Journey-to-the-West\05_构建脚本\_patch_p61_70.json',
          'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n生成 patch: {len(changes)} 处修改，{len(skipped)} 处跳过")
