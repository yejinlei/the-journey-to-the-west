"""按 key 匹配，将 _baihua_mapping.json 中的真白话写回 read.json 的 text_zh。

- key 格式：page_id#md5(text[:20]).hexdigest()[:8]
- 应用后同步更新 char_count 字段为 text_zh 的实际长度
- 用与 _scan_gubao_fake.py 相同的算法验证伪白话 = 0
"""
import json
import re
import sys
from pathlib import Path
from hashlib import md5


def build_key(pid: str, text: str) -> str:
    return pid + "#" + md5((text or "")[:20].encode("utf-8")).hexdigest()[:8]


# --- 伪白话判定（与 _scan_gubao_fake.py 完全一致） ---
TRAD_TO_SIMP = {
    '東': '东', '龍': '龙', '鳳': '凤', '漢': '汉', '經': '经', '國': '国',
    '書': '书', '讀': '读', '說': '说', '時': '时', '後': '后', '麼': '么',
    '這': '这', '們': '们', '個': '个', '頭': '头', '髮': '发', '鬚': '须',
    '見': '见', '開': '开', '關': '关', '問': '问', '題': '题', '話': '话',
    '語': '语', '誰': '谁', '過': '过', '會': '会', '於': '于', '為': '为',
    '來': '来', '去': '去', '西': '西', '南': '南', '北': '北', '門': '门',
    '學': '学', '寫': '写', '畫': '画', '中': '中', '人': '人',
}


def simp_from_trad(s: str) -> str:
    return "".join(TRAD_TO_SIMP.get(c, c) for c in s)


def norm(s: str) -> str:
    return re.sub(r"[\s，。、「」『』：；？！.,:;!?()\[\]\"'\-—…～]+", "", s or "")


def is_fake(text: str, text_zh: str) -> bool:
    if not text or not text_zh:
        return False
    a = norm(text_zh)
    b = norm(simp_from_trad(text))
    if not a or not b:
        return False
    prefix_len = min(60, len(a), len(b))
    common = sum(1 for x, y in zip(a[:prefix_len], b[:prefix_len]) if x == y)
    return common / max(prefix_len, 1) >= 0.85


def main() -> int:
    data_path = Path("docs/data/pages/read.json")
    mapping_path = Path("_baihua_mapping.json")

    data = json.loads(data_path.read_text(encoding="utf-8"))
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    lines = data["lines"]

    print(f"loaded read.json: {len(lines)} lines")
    print(f"loaded mapping: {len(mapping)} entries")

    # 建 key -> {text, index_in_lines} 索引
    key_index = {}
    for i, l in enumerate(lines):
        if l.get("edition") != "gubao":
            continue
        txt = l.get("text", "") or ""
        k = build_key(l["page_id"], txt)
        # 同一 key 可能出现多次，全部登记
        key_index.setdefault(k, []).append(i)

    print(f"indexed unique keys: {len(key_index)}")

    # 应用映射
    hit = 0
    miss = []
    for k, zh in mapping.items():
        if k not in key_index:
            miss.append(k)
            continue
        for idx in key_index[k]:
            lines[idx]["text_zh"] = zh
            lines[idx]["char_count"] = len(zh)
            hit += 1
    print(f"applied to {hit} rows")
    if miss:
        print(f"MISS ({len(miss)}): {miss}")

    # 验证：跑伪白话扫描（与 _scan_gubao_fake.py 的 is_title_or_poem 一致）
    def _is_title_or_poem(l):
        ft = l.get("form_type", "")
        if ft in ("title", "poem", "poem_start", "poem_end", "couplet"):
            return True
        txt = l.get("text", "") or ""
        if txt.startswith("第一") or txt.startswith("第二"):
            return True
        return False

    fake_after = []
    for i, l in enumerate(lines):
        if l.get("edition") != "gubao":
            continue
        if _is_title_or_poem(l):
            continue
        txt = l.get("text", "") or ""
        if len(txt) < 10:  # 与 _dump_fake_keys.py 一致：短标题（如"木母空"）不判定
            continue
        if is_fake(txt, l.get("text_zh", "")):
            fake_after.append((i, l["page_id"], l.get("form_type", ""), (l.get("text", "") or "")[:40]))
    print(f"fake AFTER apply: {len(fake_after)}")
    if fake_after:
        print("sample:")
        for item in fake_after[:10]:
            print(" ", item)

    # 写回
    data_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"written {data_path}")
    return 0 if not fake_after else 1


if __name__ == "__main__":
    sys.exit(main())
