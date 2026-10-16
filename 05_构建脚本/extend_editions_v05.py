# -*- coding: utf-8 -*-
"""扩版本 v0.9：并入 6 个新版本正文 + 4 个 PDF 占位版本元数据。

新增版本：
  xiyouji_zhuan   —— 杨致和《西游记传》（简本，4卷41则）
  xiyou_yuanzhi   —— 刘一明《西游原旨》（丹道评点，100回诗诀）
  xiyou_bu        —— 董说《西游补》（16回+序）
  hou_xiyouji     —— 《后西游记》（40回+序）
  xu_xiyouji      —— 《续西游记》（100回+序）
  yangdonglai_ping —— 杨东来批评西游记（PDF占位，仅元数据）

PDF 占位版本（仅 editions 元数据，无章节/行）：
  qujing_shihua    —— 大唐三藏取经诗话
  xindiao_qujingji —— 新雕大唐三藏法师取经记
  xiyouji_kaozheng —— 胡适《西游记考证》

同时：
  - editions.parquet 新增 category 列（正传底本/简本/评点/续书/补书/文献）
  - edition_lineage.parquet 追加 5 条谱系边

跑法：
  python extend_editions_v05.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "04_knowledge_data"
DOCS = ROOT / "docs" / "data"
TXT = ROOT / "06_文本源" / "wiki" / "txt"
RAW = ROOT / "06_文本源" / "wiki" / "raw"

now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

# ---------- 版元数据 ----------
NEW_EDITIONS = [
    dict(edition_id="xiyouji_zhuan", display_name="楊致和《西游記傳》", year=-1,
         publisher="明 楊致和", category="简本",
         desc="三大簡本之一，4卷41則，與朱鼎臣《釋厄傳》互證簡本系統"),
    dict(edition_id="xiyou_yuanzhi", display_name="劉一明《西游原旨》", year=-1,
         publisher="清 劉一明", category="评点",
         desc="清代丹道評點代表，100回每回一首丹道詩訣，闡三教一家之理"),
    dict(edition_id="xiyou_bu", display_name="董說《西游補》", year=1641,
         publisher="明 董說", category="补书",
         desc="16回，插入火焰山之後的補敘衍生，文學價值極高"),
    dict(edition_id="hou_xiyouji", display_name="《後西游記》", year=-1,
         publisher="清 天花才子評點", category="续书",
         desc="40回，孫小聖/豬一戒二代取經"),
    dict(edition_id="xu_xiyouji", display_name="《續西游記》", year=-1,
         publisher="清 佚名", category="续书",
         desc="100回，取經東還故事"),
    # PDF 占位版（仅元数据，无章节/行）
    dict(edition_id="yangdonglai_ping", display_name="楊東來先生批評西游記", year=-1,
         publisher="明 楊訥", category="评点",
         desc="元末明初雜劇，6卷，維基僅PDF掃描占位，待OCR"),
    dict(edition_id="qujing_shihua", display_name="《大唐三藏取經詩話》", year=-1,
         publisher="宋刊", category="文献",
         desc="西游故事最早文本形態之一，維基PDF占位"),
    dict(edition_id="xindiao_qujingji", display_name="《新雕大唐三藏法師取經記》", year=-1,
         publisher="宋刊", category="文献",
         desc="取經詩話系統異本，維基PDF占位"),
    dict(edition_id="xiyouji_kaozheng", display_name="胡適《西游記考證》", year=1923,
         publisher="胡適", category="文献",
         desc="現代西游版本學奠基文獻，維基PDF占位"),
]

# ---------- 旧版 category 回填 ----------
EDITION_CATEGORY_BACKFILL = {
    "shidetang": "正传底本",
    "gubao": "正传底本",
    "li_ping": "评点",
    "daqishi": "评点",
    "xinke_pingbi": "评点",
    "zhenquan": "评点",
    "yangminzhai": "正传底本",
    "minzhaitang": "正传底本",
    "zhengdao": "评点",
    "baihui_xiangzhu": "评点",
    "zhu_ping": "简本",
}

# ---------- 谱系边 ----------
NEW_LINEAGE = [
    dict(lineage_id="lineage-010", from_edition="shidetang", to_edition="xiyouji_zhuan",
         lineage_type="简本", note="楊致和《西游記傳》4卷41則，簡本系統第三種"),
    dict(lineage_id="lineage-011", from_edition="zhenquan", to_edition="xiyou_yuanzhi",
         lineage_type="加评", note="劉一明丹道評點，真詮/證道評點系統之流"),
    dict(lineage_id="lineage-012", from_edition="shidetang", to_edition="xiyou_bu",
         lineage_type="补书", note="董說補敘，插於火焰山之後"),
    dict(lineage_id="lineage-013", from_edition="shidetang", to_edition="hou_xiyouji",
         lineage_type="续书", note="二代取經衍生小說"),
    dict(lineage_id="lineage-014", from_edition="shidetang", to_edition="xu_xiyouji",
         lineage_type="续书", note="取經東還衍生小說"),
]

# ---------- 工具函数 ----------
VERSE_MARKERS = [
    "詩曰", "詞曰", "賦曰", "歌曰", "詩云", "詞云", "賦云", "歌云",
    "有詩為證", "有賦為證", "有偈為證", "西江月", "滿庭芳", "沁園春",
]
HUI_TITLE_RE = re.compile(r"^第([一二三四五六七八九十百零〇0-9]+)回[\s　]+(.+?)\s*$")
H2_RE = re.compile(r"^==\s*(.+?)\s*==\s*$", re.M)


def han2num(s: str) -> int:
    """中文数字转阿拉伯（支持 1-100）。"""
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if "百" in s:
        parts = s.split("百")
        return digits.get(parts[0], 1) * 100 + (han2num(parts[1]) if parts[1] else 0)
    if "十" in s:
        parts = s.split("十")
        tens = digits.get(parts[0], 1) if parts[0] else 1
        ones = digits.get(parts[1], 0) if parts[1] else 0
        return tens * 10 + ones
    return digits.get(s, -1)


def han2num_to_str(n: int) -> str:
    d = "零一二三四五六七八九"
    if n == 100:
        return "一百"
    if n < 10:
        return d[n]
    tens = n // 10
    ones = n % 10
    if tens == 1:
        return "十" + (d[ones] if ones else "")
    return f"{d[tens]}十" + (d[ones] if ones else "")


def split_paragraphs(text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if b.strip()]


def classify_para(p: str) -> tuple[str, bool]:
    """返回 (form_type, is_commentary)。"""
    p = p.strip()
    if not p:
        return "main", False
    if p.startswith("第") and "回" in p[:8]:
        return "title", False
    if p.startswith("卷") and ("之" in p[:4] or p[1].isdigit()):
        return "title", False
    if p.startswith("序") and len(p) < 30:
        return "title", False
    for m in VERSE_MARKERS:
        if m in p[:10]:
            return "verse", False
    if p.startswith(":") or p.startswith("："):
        return "verse", False
    return "main", False


# ---------- 通用回-style 处理 ----------
def process_hui_style(eid: str, txt_files: list[tuple[int, str]], vol_label: str = "") -> tuple[list[dict], list[dict], list[dict]]:
    """通用：西游补/后西游/续西游。
    txt_files: [(seq, filename), ...] 按 seq 排序
    """
    chapters, lines_all, pages = [], [], []

    for seq, fname in txt_files:
        f = TXT / fname
        if not f.exists():
            print(f"  [skip] 缺文件: {fname}")
            continue
        text = f.read_text(encoding="utf-8")
        paras = split_paragraphs(text)

        # 从文本中提取回目标题
        chap_title = ""
        chap_label = ""
        for p in paras[:3]:
            m = HUI_TITLE_RE.match(p)
            if m:
                n = han2num(m.group(1))
                chap_label = f"第{han2num_to_str(n)}回" if n > 0 else f"第{n}回"
                chap_title = m.group(2).strip()
                break
        if not chap_label:
            # 序等非回页
            if seq == 0:
                chap_label = "序"
                chap_title = paras[0][:30] if paras else ""
            else:
                chap_label = f"第{seq}页"

        chapter_id = f"{eid}/{seq:03d}"
        page_id = f"{eid}#c{seq:03d}"
        page_no = seq

        lines_local = []
        for li, para in enumerate(paras):
            line_id = f"{eid}#c{seq:03d}#L{li:03d}"
            ft, is_com = classify_para(para)
            lines_local.append(dict(
                line_id=line_id, page_id=page_id, edition=eid,
                page_no=page_no, line_idx=li,
                form_type=ft,
                text=para[:2000],
                char_count=len(para),
                confidence=0.9,
                is_commentary=is_com,
            ))

        chapters.append(dict(
            chapter_id=chapter_id, edition=eid,
            chapter_label=chap_label,
            chapter_title=chap_title,
            raw_title=f"{vol_label} {chap_label} {chap_title}".strip(),
            first_page=page_no,
            first_line_id=f"{eid}#c{seq:03d}#L000",
        ))

        pages.append(dict(
            page_id=page_id, edition=eid,
            edition_dirname=eid, page_no=page_no, page_order=page_no,
            dc_source=f"{eid}\\{fname}",
            dc_title=f"{eid} {chap_label} {chap_title}",
            layout="text_from_wikisource",
            line_count=len(lines_local),
            char_count=sum(x["char_count"] for x in lines_local),
            main_line_count=sum(1 for x in lines_local if x["form_type"] == "main"),
            commentary_line_count=sum(1 for x in lines_local if x["is_commentary"]),
            entity_count=0, relation_count=0, event_count=0,
            chapter_ref=chap_label,
            model="wikisource-api", generated_at=now,
            ocr_seconds=0.0, annotation_seconds=0.0,
        ))
        lines_all.extend(lines_local)

    return chapters, lines_all, pages


# ---------- 西游补 ----------
def process_xiyou_bu() -> tuple[list[dict], list[dict], list[dict]]:
    """西游补：序 + 16回。"""
    eid = "xiyou_bu"
    # 读 titles json 获取实际文件名
    titles_file = ROOT / "06_文本源" / "wiki" / f"titles_{eid}.json"
    with titles_file.open(encoding="utf-8") as f:
        toc = json.load(f)

    txt_files = []
    for item in toc:
        title = item["title"]  # e.g. "西遊補/序" or "西遊補/第一回"
        fname = f"{eid}_p{item['idx']:03d}.txt"
        if "序" in title:
            seq = 0
        else:
            m = re.search(r"第([一二三四五六七八九十]+)回", title)
            seq = han2num(m.group(1)) if m else item["idx"]
        txt_files.append((seq, fname))
    txt_files.sort(key=lambda x: x[0])
    return process_hui_style(eid, txt_files)


# ---------- 后西游记 ----------
def process_hou_xiyouji() -> tuple[list[dict], list[dict], list[dict]]:
    """后西游记：序 + 40回。"""
    eid = "hou_xiyouji"
    titles_file = ROOT / "06_文本源" / "wiki" / f"titles_{eid}.json"
    with titles_file.open(encoding="utf-8") as f:
        toc = json.load(f)

    txt_files = []
    for item in toc:
        title = item["title"]
        fname = f"{eid}_p{item['idx']:03d}.txt"
        if "序" in title:
            seq = 0
        else:
            m = re.search(r"第([一二三四五六七八九十]+)回", title)
            seq = han2num(m.group(1)) if m else item["idx"]
        txt_files.append((seq, fname))
    txt_files.sort(key=lambda x: x[0])
    return process_hui_style(eid, txt_files)


# ---------- 续西游记 ----------
def process_xu_xiyouji() -> tuple[list[dict], list[dict], list[dict]]:
    """续西游记：序 + 100回。"""
    eid = "xu_xiyouji"
    titles_file = ROOT / "06_文本源" / "wiki" / f"titles_{eid}.json"
    with titles_file.open(encoding="utf-8") as f:
        toc = json.load(f)

    txt_files = []
    for item in toc:
        title = item["title"]
        fname = f"{eid}_p{item['idx']:03d}.txt"
        if "序" in title:
            seq = 0
        else:
            m = re.search(r"第(\d+)回", title)
            seq = int(m.group(1)) if m else item["idx"]
        txt_files.append((seq, fname))
    txt_files.sort(key=lambda x: x[0])
    return process_hui_style(eid, txt_files)


# ---------- 西游原旨 ----------
def process_xiyou_yuanzhi() -> tuple[list[dict], list[dict], list[dict]]:
    """西游原旨：单页，100回每回一首丹道诗。
    按 === 切分为 100 章 + 序/读法/诗结等。
    """
    eid = "xiyou_yuanzhi"
    f = TXT / f"{eid}_p001.txt"
    text = f.read_text(encoding="utf-8")

    # 按 ### 切分（H3 被转为 ###）
    sections = re.split(r"\n###\s+", text)

    chapters, lines_all, pages = [], [], []
    seq = 0

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        # 判断是否为回目
        m = re.match(r"^(第[一二三四五六七八九十百零〇0-9]+回)\s*　*(.+?)(?:\n|$)", sec)
        if m:
            seq += 1
            hui_num = m.group(1)
            hui_title = m.group(2).strip()
            chap_label = hui_num
            chap_title = hui_title
        else:
            # 序/读法/诗结等非回部分
            if seq == 0:
                chap_label = "序"
                chap_title = sec.split("\n")[0][:30]
            else:
                chap_label = f"附{seq}"
                chap_title = sec.split("\n")[0][:30]
            seq += 1

        chapter_id = f"{eid}/{seq:03d}"
        page_id = f"{eid}#c{seq:03d}"
        page_no = seq

        paras = split_paragraphs(sec)
        lines_local = []
        for li, para in enumerate(paras):
            line_id = f"{eid}#c{seq:03d}#L{li:03d}"
            ft, is_com = classify_para(para)
            # 西游原旨的每回内容都是评点性质
            if seq > 0 and not chap_label.startswith("序"):
                is_com = True
                if ft == "main":
                    ft = "commentary"
            lines_local.append(dict(
                line_id=line_id, page_id=page_id, edition=eid,
                page_no=page_no, line_idx=li,
                form_type=ft,
                text=para[:2000],
                char_count=len(para),
                confidence=0.85,
                is_commentary=is_com,
            ))

        chapters.append(dict(
            chapter_id=chapter_id, edition=eid,
            chapter_label=chap_label,
            chapter_title=chap_title,
            raw_title=f"{chap_label} {chap_title}",
            first_page=page_no,
            first_line_id=f"{eid}#c{seq:03d}#L000",
        ))

        pages.append(dict(
            page_id=page_id, edition=eid,
            edition_dirname=eid, page_no=page_no, page_order=page_no,
            dc_source=f"{eid}\\{eid}_p001.txt",
            dc_title=f"{eid} {chap_label} {chap_title}",
            layout="text_from_wikisource",
            line_count=len(lines_local),
            char_count=sum(x["char_count"] for x in lines_local),
            main_line_count=sum(1 for x in lines_local if x["form_type"] == "main"),
            commentary_line_count=sum(1 for x in lines_local if x["is_commentary"]),
            entity_count=0, relation_count=0, event_count=0,
            chapter_ref=chap_label,
            model="wikisource-api", generated_at=now,
            ocr_seconds=0.0, annotation_seconds=0.0,
        ))
        lines_all.extend(lines_local)

    return chapters, lines_all, pages


# ---------- 西游记传 ----------
def process_xiyouji_zhuan() -> tuple[list[dict], list[dict], list[dict]]:
    """西游记传：4卷41则。
    从 raw 文件提取 H2 标题作为"则"边界，从 txt 文件取正文。
    """
    eid = "xiyouji_zhuan"
    vol_labels = {1: "卷之一", 2: "卷之二", 3: "卷之三", 4: "卷之四"}
    chapters, lines_all, pages = [], [], []
    ze_no = 0

    for vol in range(1, 5):
        raw_f = RAW / f"{eid}_p{vol:03d}.txt"
        txt_f = TXT / f"{eid}_p{vol:03d}.txt"
        raw_text = raw_f.read_text(encoding="utf-8")
        txt_text = txt_f.read_text(encoding="utf-8")

        # 从 raw 提取 H2 标题
        h2_titles = H2_RE.findall(raw_text)

        # 按 ## 切分 txt（strip_wiki_markup 把 == 转为 ##）
        sections = re.split(r"\n##\s+\x01\n", txt_text)

        if len(sections) != len(h2_titles) + 1:
            # 第一则前面的序文
            print(f"  [warn] 卷{vol}: {len(h2_titles)} 标题 vs {len(sections)} 段")

        # 序文部分（第一则之前的内容）
        preamble = sections[0] if sections else ""

        for zi, h2_title in enumerate(h2_titles):
            ze_no += 1
            sec_text = sections[zi + 1] if zi + 1 < len(sections) else ""

            chap_label = f"第{ze_no}則"
            chap_title = h2_title.strip()
            chapter_id = f"{eid}/{ze_no:03d}"
            page_id = f"{eid}#c{ze_no:03d}"
            page_no = ze_no

            paras = split_paragraphs(sec_text)
            lines_local = []
            for li, para in enumerate(paras):
                line_id = f"{eid}#c{ze_no:03d}#L{li:03d}"
                ft, is_com = classify_para(para)
                lines_local.append(dict(
                    line_id=line_id, page_id=page_id, edition=eid,
                    page_no=page_no, line_idx=li,
                    form_type=ft,
                    text=para[:2000],
                    char_count=len(para),
                    confidence=0.9,
                    is_commentary=is_com,
                ))

            vol_label = vol_labels.get(vol, f"卷{vol}")
            chapters.append(dict(
                chapter_id=chapter_id, edition=eid,
                chapter_label=chap_label,
                chapter_title=chap_title,
                raw_title=f"{vol_label} {chap_label} {chap_title}",
                first_page=page_no,
                first_line_id=f"{eid}#c{ze_no:03d}#L000",
            ))

            pages.append(dict(
                page_id=page_id, edition=eid,
                edition_dirname=eid, page_no=page_no, page_order=page_no,
                dc_source=f"{eid}\\{eid}_p{vol:03d}.txt",
                dc_title=f"{eid} {vol_label} {chap_label} {chap_title}",
                layout="text_from_wikisource",
                line_count=len(lines_local),
                char_count=sum(x["char_count"] for x in lines_local),
                main_line_count=sum(1 for x in lines_local if x["form_type"] == "main"),
                commentary_line_count=0,
                entity_count=0, relation_count=0, event_count=0,
                chapter_ref=chap_label,
                model="wikisource-api", generated_at=now,
                ocr_seconds=0.0, annotation_seconds=0.0,
            ))
            lines_all.extend(lines_local)

    return chapters, lines_all, pages


# ---------- 合并 & 落盘 ----------
def merge_and_write(old: pd.DataFrame, new_rows: list[dict], fname: str, key: str) -> pd.DataFrame:
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df_new[key] = df_new[key].astype(str)
        old[key] = old[key].astype(str)
        for c in df_new.columns:
            if c not in old.columns:
                old[c] = pd.NA
        for c in old.columns:
            if c not in df_new.columns:
                df_new[c] = pd.NA
        merged = pd.concat([old, df_new], ignore_index=True)
        merged = merged.drop_duplicates(subset=[key], keep="first").reset_index(drop=True)
    else:
        merged = old
    return merged


def main() -> int:
    if not sys.stdout.encoding or sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    ed_old = pd.read_parquet(BASE / "editions.parquet")
    ch_old = pd.read_parquet(BASE / "chapters.parquet")
    ln_old = pd.read_parquet(BASE / "lines.parquet")
    pg_old = pd.read_parquet(BASE / "pages.parquet")

    print(f"旧: editions={len(ed_old)} chapters={len(ch_old)} lines={len(ln_old)} pages={len(pg_old)}")

    # 1) editions: 先回填 category，再 merge 新版
    if "category" not in ed_old.columns:
        ed_old["category"] = pd.NA
    for eid, cat in EDITION_CATEGORY_BACKFILL.items():
        ed_old.loc[ed_old["edition_id"] == eid, "category"] = cat

    ed = merge_and_write(ed_old, NEW_EDITIONS, "editions.parquet", "edition_id")

    # 2) 逐版处理
    all_ch, all_ln, all_pg = [], [], []

    processors = [
        ("xiyouji_zhuan", process_xiyouji_zhuan),
        ("xiyou_yuanzhi", process_xiyou_yuanzhi),
        ("xiyou_bu", process_xiyou_bu),
        ("hou_xiyouji", process_hou_xiyouji),
        ("xu_xiyouji", process_xu_xiyouji),
    ]

    for eid, proc in processors:
        print(f"\n处理 [{eid}] ...")
        try:
            ch, ln, pg = proc()
            print(f"  chapters={len(ch)} lines={len(ln)} pages={len(pg)}")
            all_ch.extend(ch)
            all_ln.extend(ln)
            all_pg.extend(pg)
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # 3) 合并
    ch = merge_and_write(ch_old, all_ch, "chapters.parquet", "chapter_id")
    ln = merge_and_write(ln_old, all_ln, "lines.parquet", "line_id")
    pg = merge_and_write(pg_old, all_pg, "pages.parquet", "page_id")

    print(f"\n合并后: editions={len(ed)} chapters={len(ch)} lines={len(ln)} pages={len(pg)}")

    # 4) 落盘
    for name, df in [("editions", ed), ("chapters", ch), ("lines", ln), ("pages", pg)]:
        df.to_parquet(BASE / f"{name}.parquet", index=False)
        df.to_parquet(DOCS / f"{name}.parquet", index=False)

    print("\n落盘完成：")
    for name in ["editions", "chapters", "lines", "pages"]:
        p = BASE / f"{name}.parquet"
        print(f"  {name}: {p.stat().st_size/1024:.1f} KB")

    # 5) 追加谱系边
    lineage_file = BASE / "edition_lineage.parquet"
    if lineage_file.exists():
        lg_old = pd.read_parquet(lineage_file)
        lg = merge_and_write(lg_old, NEW_LINEAGE, "edition_lineage.parquet", "lineage_id")
        lg.to_parquet(BASE / "edition_lineage.parquet", index=False)
        lg.to_parquet(DOCS / "edition_lineage.parquet", index=False)
        print(f"\n谱系边: {len(lg)} 条（新增 {len(NEW_LINEAGE)} 条）")
    else:
        print("\n[warn] edition_lineage.parquet 不存在，跳过谱系追加")

    # 6) 校验
    print("\n按 edition 分布：")
    for f in ["chapters", "lines", "pages"]:
        df = pd.read_parquet(BASE / f"{f}.parquet")
        vc = df["edition"].value_counts().to_dict()
        print(f"  {f}: {vc}")

    # category 分布
    ed_df = pd.read_parquet(BASE / "editions.parquet")
    cat_counts = ed_df["category"].value_counts(dropna=False).to_dict()
    print(f"\ncategory 分布: {cat_counts}")

    # 新增版本 form_type 分布
    for eid in ["xiyou_bu", "hou_xiyouji", "xu_xiyouji", "xiyou_yuanzhi", "xiyouji_zhuan"]:
        df = pd.read_parquet(BASE / "lines.parquet")
        sub = df[df["edition"] == eid]
        if len(sub) > 0:
            ft = sub["form_type"].value_counts().to_dict()
            total_chars = int(sub["char_count"].sum())
            print(f"  [{eid}] form_type={ft} 总字数={total_chars:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
