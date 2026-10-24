"""p81-p90 精校：字级替换 + p87L6 整段幻觉回滚。"""
import json

READ = r'f:\src\The-Journey-to-the-West\docs\data\pages\read.json'
d = json.load(open(READ, encoding='utf-8'))

# (page, line, old, new, reason)
CORRECTIONS = [
    (86, 3, "做一個兒看", "做一个儿看",
     "繁简错混：译文本为简体段落，末尾混入繁体'個兒'"),
    (86, 6, "也说得上", "也说得是",
     "错译：原文'也說得是'意为'这话有道理'，'说得上'是另一个词"),
    (86, 9, "吓得以至南山大王", "吓得南山大王",
     "衍字：原文'諕得那南山大王滾風生霧'，无'以至'"),
    (87, 3, "吓得以至檐下冠带者", "吓得檐下冠带者",
     "衍字：原文'諕得那簷下冠帶者'，无'以至'"),
]

# 整段回滚：p87L6 译文开头被幻觉污染（把"三藏到府吃饭"错写成"丑和尚对话"）
# 原文：师徒到府—看茶摆斋—八戒暴食—唐僧谢斋问郡侯—郡侯吟诗道谢
# 译文开头错为："郡侯即命看茶摆斋，少顷，行者回观圣意。那公人请他同坐，不敢抬头瞻视……
#         '这个和尚，原来是个丑人！'……'我本西洋者，要往东土寻佛经。'"
# 修正：恢复原文语义，仅替换开头一段（郡侯吟诗起前的部分），后段（郡侯诗 + 行者应答 + 请龙雨）保留
P87L6_OLD_HEAD = "郡侯即命看茶摆斋，少顷，行者回观圣意。那公人请他同坐，不敢抬头瞻视，只看他 那面皮，黑如浓墨；眼有金光，头无发迹。心中自念道：“这个 和尚，原来是个丑人！”行者看得他那样子，也自道：“原来是个 蠢物！”当时郡侯开言便问：“圣僧自那方来？要往何处去？”行者道：“我本西洋者，要往东土寻佛经。”郡侯道："
P87L6_NEW_HEAD = "郡侯即命看茶摆斋，少顷斋至。那八戒放量吞餐，如同饿虎。吓得那些捧盘的心惊胆战，一往一来，添汤添饭，就如走马灯儿一般，刚刚供上，直吃得饱满方休。斋毕，唐僧谢了斋，却问：“郡侯大人，贵处干旱几时了？”郡侯道："

lines_by_key = {}
for l in d['lines']:
    if l['edition'] == 'gubao':
        lines_by_key[(l['page_no'], l['line_idx'])] = l

changes = []
skipped = []

# 字级替换
for page, line, old, new, reason in CORRECTIONS:
    key = (page, line)
    if key not in lines_by_key:
        skipped.append((key, "行不存在"))
        continue
    zh = lines_by_key[key].get('text_zh', '')
    cnt = zh.count(old)
    if cnt == 0:
        skipped.append((key, f"'{old}' 未在 text_zh 中找到"))
        continue
    if cnt > 1:
        skipped.append((key, f"'{old}' 出现 {cnt} 次，非唯一，跳过"))
        continue
    new_zh = zh.replace(old, new)
    changes.append({"page": page, "line": line, "text_zh": new_zh})
    print(f"✓ p{page}L{line}: '{old}' → '{new}'  ({reason})")

# p87L6 整段回滚
key = (87, 6)
if key in lines_by_key:
    zh = lines_by_key[key].get('text_zh', '')
    if P87L6_OLD_HEAD in zh:
        new_zh = zh.replace(P87L6_OLD_HEAD, P87L6_NEW_HEAD)
        changes.append({"page": 87, "line": 6, "text_zh": new_zh})
        print(f"✓ p87L6: 整段幻觉回滚（开头段恢复为原文语义）")
    else:
        skipped.append((key, "整段幻觉开头片段未匹配，可能是格式差异"))
        # 打印前 200 字符供诊断
        print("  诊断前 300 字:", zh[:300])

for s in skipped:
    print(f"✗ p{s[0][0]}L{s[0][1]}: {s[1]}")

out = {"batch": "p81_90", "changes": changes}
with open(r'f:\src\The-Journey-to-the-West\05_构建脚本\_patch_p81_90.json',
          'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n生成 patch: {len(changes)} 处修改，{len(skipped)} 处跳过")
