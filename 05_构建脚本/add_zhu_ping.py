# -*- coding: utf-8 -*-
"""将朱鼎臣《唐三藏西游释厄传》（zhu_ping）66 章并入知识图谱。

数据源：06_文本源/diancang/txt/ 下 66 个 .txt 文件（由 fetch_zhu_ping.py 抓取）
目录：  06_文本源/diancang/titles.json

只做轻量入图，不做实体/事件抽取：
  editions.parquet  += 1 行（zhu_ping）
  chapters.parquet  += 66 行（每回一行，含卷标）
  lines.parquet     += N 行（每段落一行，含引诗、正文、朱评批注）
  pages.parquet     += 66 行（每回作为一页，无图像）

朱评本正文特征：
  - 段落以"右言古调："起，"有诗为证"/"有赋为证"/"有偈为证"后接四/八句
  - 朱评以括号形式内嵌在正文中，如"（茫原作"忙"）"（此系后世点校本加的校勘记）
  - 因无 OCR 源，confidence=1.0（原始文本）
  - form_type: title（卷标或题头） / verse（诗词赋偈） / main（正文）

跑法：
  python 05_构建脚本/add_zhu_ping.py
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
TXT = ROOT / "06_文本源" / "diancang" / "txt"
TOC_JSON = ROOT / "06_文本源" / "diancang" / "titles.json"

now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

# ---------- 卷标映射（与 fetch_zhu_ping.py 保持一致） ----------
VOLUME_MAP = [
    (70992, 70995, "卷之一"),
    (70996, 71001, "卷之二"),
    (71002, 71009, "卷之三"),
    (71010, 71017, "卷之四"),
    (71018, 71023, "卷之五"),
    (71024, 71032, "卷之六"),
    (71033, 71038, "卷之七"),
    (71039, 71041, "卷之八"),
    (71042, 71050, "卷之九"),
    (71051, 71057, "卷之十"),
]


def get_volume(cid: int) -> str:
    for lo, hi, vol in VOLUME_MAP:
        if lo <= cid <= hi:
            return vol
    return ""


# ---------- 版元数据 ----------
NEW_EDITION = dict(
    edition_id="zhu_ping",
    display_name="朱评本（朱鼎臣）",
    year=-1,
    publisher="明朱鼎臣",
    desc="明《唐三藏西游释厄传》，10 卷 67 回本（典藏拆为 66 章），11.5 万字，"
         "由陈士奇《西游真诠》所据之底本系统",
)

# ---------- 段落 form_type 判定 ----------
VERSE_MARKERS = [
    "有诗为证", "有赋为证", "有偈为证", "词曰", "诗曰", "赋曰", "词云", "诗云",
    "赋云", "歌曰", "歌云", "右言古调", "西江月", "满庭芳", "沁园春", "临江仙",
]
TITLE_RE = re.compile(r"^(第[一二三四五六七八九十百零〇]+回|卷之[一二三四五六七八九十])")
# 章节首题（如"灵根育生源流出"）
CHAPTER_TITLE_RE = re.compile(r"^[\u4e00-\u9fff]{4,15}$")


def classify(para: str) -> str:
    """判断段落 form_type。"""
    p = para.strip()
    if not p:
        return "main"
    if TITLE_RE.match(p):
        return "title"
    # 诗词标记
    for m in VERSE_MARKERS:
        if m in p[:10]:
            return "verse"
    # 短行且以标点收尾，可能是诗句（四言/七言/杂言）
    # 保守起见仅标记明确的诗句开头
    return "main"


def is_commentary(para: str) -> bool:
    """朱评本无独立评点栏，校勘记以（）内嵌，不计为 commentary。"""
    return False


# ---------- 主流程 ----------
def load_toc() -> list[dict]:
    """从 titles.json 读 TOC（fetch_zhu_ping.py 的产物）。"""
    with TOC_JSON.open(encoding="utf-8") as f:
        return json.load(f)


def process_zhu_ping() -> tuple[list[dict], list[dict], list[dict]]:
    chapters, lines_all, pages = [], [], []
    eid = "zhu_ping"

    for item in load_toc():
        cid = item["chapter_id"]
        ch_no = item["chapter_no"]
        title = item["title"]
        volume = get_volume(cid)
        fname = f"{cid}_{title}.txt"
        txt_path = TXT / fname
        if not txt_path.exists():
            print(f"  [skip] 缺文件: {fname}")
            continue

        text = txt_path.read_text(encoding="utf-8")
        # 段落切分：按单换行切（fetch_zhu_ping.py 已按行输出）
        paras = [ln.strip() for ln in text.splitlines() if ln.strip()]

        chap_label = f"第{ch_no}回"
        chapter_id = f"{eid}/{ch_no:03d}"
        page_id = f"{eid}#c{ch_no:03d}"
        page_no = ch_no

        # 卷标作为章首 line（title）
        lines_local = []
        first_vol_idx = -1
        for li, para in enumerate(paras):
            line_id = f"{eid}#c{ch_no:03d}#L{li:03d}"
            ft = classify(para)
            is_com = is_commentary(para)
            lines_local.append(dict(
                line_id=line_id, page_id=page_id, edition=eid,
                page_no=page_no, line_idx=li,
                form_type=ft,
                text=para[:2000],
                char_count=len(para),
                confidence=1.0,
                is_commentary=is_com,
            ))

        chapters.append(dict(
            chapter_id=chapter_id, edition=eid,
            chapter_label=chap_label,
            chapter_title=title,
            raw_title=f"{volume} {chap_label} {title}".strip(),
            first_page=page_no,
            first_line_id=f"{eid}#c{ch_no:03d}#L000",
        ))

        char_count_total = sum(x["char_count"] for x in lines_local)
        main_count = sum(1 for x in lines_local if x["form_type"] == "main")
        verse_count = sum(1 for x in lines_local if x["form_type"] == "verse")
        comment_count = sum(1 for x in lines_local if x["is_commentary"])

        pages.append(dict(
            page_id=page_id, edition=eid,
            edition_dirname=eid, page_no=page_no, page_order=page_no,
            dc_source=f"{eid}\\c{ch_no:03d}.txt",
            dc_title=f"{eid} {volume} {chap_label} {title}",
            layout="text_from_diancang",
            line_count=len(lines_local),
            char_count=char_count_total,
            main_line_count=main_count,
            commentary_line_count=comment_count,
            entity_count=0, relation_count=0, event_count=0,
            chapter_ref=chap_label,
            model="diancang-html-extract",
            generated_at=now,
            ocr_seconds=0.0, annotation_seconds=0.0,
        ))

        lines_all.extend(lines_local)
        print(f"  {ch_no:>2}/66  {volume}  {chap_label} {title[:14]:14s}  "
              f"lines={len(lines_local):>3d}  chars={char_count_total:>5d}")

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
    print("\n抓取朱评本入表：")

    ch_new, ln_new, pg_new = process_zhu_ping()
    print(f"\n新-朱评本: chapters={len(ch_new)} lines={len(ln_new)} pages={len(pg_new)}")

    ed = merge_and_write(ed_old, [NEW_EDITION], "editions.parquet", "edition_id")
    ch = merge_and_write(ch_old, ch_new, "chapters.parquet", "chapter_id")
    ln = merge_and_write(ln_old, ln_new, "lines.parquet", "line_id")
    pg = merge_and_write(pg_old, pg_new, "pages.parquet", "page_id")

    print(f"\n合并后: editions={len(ed)} chapters={len(ch)} lines={len(ln)} pages={len(pg)}")

    for name, df in [("editions", ed), ("chapters", ch), ("lines", ln), ("pages", pg)]:
        df.to_parquet(BASE / f"{name}.parquet", index=False)
        df.to_parquet(DOCS / f"{name}.parquet", index=False)

    print("\n落盘完成：")
    for name in ["editions", "chapters", "lines", "pages"]:
        p = BASE / f"{name}.parquet"
        print(f"  {name}: {p.stat().st_size/1024:.1f} KB")

    print("\n按 edition 分布：")
    for f in ["chapters", "lines", "pages"]:
        df = pd.read_parquet(BASE / f"{f}.parquet")
        vc = df["edition"].value_counts().to_dict()
        print(f"  {f}: {vc}")

    # 朱评本内部 form_type 分布
    df = pd.read_parquet(BASE / "lines.parquet")
    sub = df[df["edition"] == "zhu_ping"]
    ft_counts = sub["form_type"].value_counts().to_dict()
    print(f"\n朱评本 form_type 分布: {ft_counts}")
    print(f"朱评本总字数: {int(sub['char_count'].sum()):,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
