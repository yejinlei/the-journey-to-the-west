# -*- coding: utf-8 -*-
"""扩版本：并入古本（gubao）与百回详注（baihui_xiangzhu）两版正文。

只做轻量入图，不做实体/事件抽取：
  editions.parquet  += 2 行
  chapters.parquet  += 200 行（每回一行）
  lines.parquet     += N 行（每段一行，含引诗、评点、正文，按空行切分）
  pages.parquet     += 200 行（每回作为一页文本，无图像）

现有 xinke_pingbi 数据保持不变。

跑法：
  python extend_editions_v04.py
"""
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

BASE = Path("04_knowledge_data")
DOCS = Path("docs/data")
TXT = Path("06_文本源") / "wiki" / "txt"
now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

# ---------- 版元数据 ----------
NEW_EDITIONS = [
    dict(edition_id="gubao", display_name="古本（維基西遊記）", year=-1,
         publisher="維基文庫", desc="世德堂系統的早期抄本，每回為一段無標題正文，含引詩、敘述"),
    dict(edition_id="baihui_xiangzhu", display_name="西遊記百回詳注", year=-1,
         publisher="清代 悟元子", desc="張世信悟元子詳注本，含每回評點，結構：標題—悟元子語—正文"),
]

# ---------- 章标题识别 ----------
TITLE_RE = re.compile(r"^第([一二三四五六七八九十百零〇]+)回[\s\u3000]+(.+?)\s*$", re.M)
# 百回详注：第N回　标题一　标题二 （中间是 U+3000 全角空格）
BH_TITLE_RE = re.compile(r"^第([一二三四五六七八九十百零〇]+)回[\u3000\s]+(.+?)\u3000(.+?)\s*$", re.M)


def han2num(s: str) -> int:
    """中文数字转阿拉伯（支持 1-100）。"""
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if s == "十":
        return 10
    if "百" in s:
        parts = s.split("百")
        return digits.get(parts[0], 1) * 100 + han2num(parts[1]) if parts[1] else 100
    if "十" in s:
        parts = s.split("十")
        tens = digits.get(parts[0], 1) if parts[0] else 1
        ones = digits.get(parts[1], 0) if parts[1] else 0
        return tens * 10 + ones
    return digits.get(s, -1)


# ---------- 段落切分 ----------
def split_paragraphs(text: str) -> list[str]:
    """按空行切成段落，去空段。"""
    blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if b.strip()]


# ---------- 逐版处理 ----------
def process_gubao() -> tuple[list[dict], list[dict], list[dict]]:
    """古本：100 回，每回一段文本，无标题。
    回标题用 "第N回"（无副标题，因为原文没有）。
    """
    chapters, lines, pages = [], [], []
    eid = "gubao"
    for i in range(1, 101):
        f = TXT / f"{eid}_p{i:03d}.txt"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        # 去掉残留模板痕迹（如 {{...}}）
        text = re.sub(r"\{\{[^}]*\}\}", "", text)
        text = re.sub(r"Category:[^\n]*", "", text)
        text = re.sub(r"<[^>]+>", "", text)

        chap_label = f"第{han2num_to_str(i)}回"  # 占位，改用 ar2cn
        chap_label = f"第{i}回"  # 简单点：用阿拉伯数字
        chapter_id = f"{eid}/{i:03d}"
        page_id = f"{eid}#c{i:03d}"
        page_no = i

        # lines: 每段落一行
        paras = split_paragraphs(text)
        for li, para in enumerate(paras):
            line_id = f"{eid}#c{i:03d}#L{li:03d}"
            ft = "verse" if (para.startswith("詩曰") or para.startswith("詞曰")
                             or para.startswith("賦曰") or ":" in para[:8]) else "main"
            if len(para) <= 40 and (para.startswith(":") or "曰：" in para[:4]):
                ft = "verse"
            lines.append(dict(
                line_id=line_id, page_id=page_id, edition=eid,
                page_no=page_no, line_idx=li,
                form_type=ft,
                text=para.replace("\n", " ")[:2000],
                char_count=len(para),
                confidence=0.9,
                is_commentary=False,
            ))

        chapters.append(dict(
            chapter_id=chapter_id, edition=eid,
            chapter_label=chap_label,
            chapter_title="",  # 古本无标题
            raw_title="",
            first_page=page_no,
            first_line_id=lines[-1]["line_id"] if False else f"{eid}#c{i:03d}#L000",
        ))

        pages.append(dict(
            page_id=page_id, edition=eid,
            edition_dirname=eid, page_no=page_no, page_order=page_no,
            dc_source=f"{eid}\\c{i:03d}.txt",
            dc_title=f"{eid} 第{i}回",
            layout="text_from_wikisource",
            line_count=len(paras),
            char_count=sum(x["char_count"] for x in lines[-len(paras):]),
            main_line_count=sum(1 for x in lines[-len(paras):] if x["form_type"] == "main"),
            commentary_line_count=0,
            entity_count=0, relation_count=0, event_count=0,
            chapter_ref=chap_label,
            model="wikisource-api", generated_at=now,
            ocr_seconds=0.0, annotation_seconds=0.0,
        ))
    return chapters, lines, pages


def han2num_to_str(n: int) -> str:
    d = "零一二三四五六七八九"
    if n == 100:
        return "一百"
    if n < 10:
        return d[n]
    tens = n // 10
    ones = n % 10
    s = ("十" if tens == 1 else f"十{d[tens]}") if ones == 0 else ""
    # simpler
    if tens == 1:
        return "十" + (d[ones] if ones else "")
    return f"{d[tens]}十" + (d[ones] if ones else "")


def process_baihui() -> tuple[list[dict], list[dict], list[dict]]:
    """百回详注：每回结构：
        <onlyinclude>
        第N回　标题一　标题二
        （悟元子语评点...）
        正文...
    """
    chapters, lines, pages = [], [], []
    eid = "baihui_xiangzhu"
    for i in range(1, 101):
        f = TXT / f"{eid}_p{i:03d}.txt"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        text = re.sub(r"<onlyinclude>|</onlyinclude>", "", text)
        text = re.sub(r"<br\s*/?>", " ", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\{\{[^}]*\}\}", "", text)
        text = re.sub(r"Category:[^\n]*", "", text)

        # 抓标题
        m = BH_TITLE_RE.search(text[:200])
        chap_title = ""
        chap_raw = ""
        if m:
            chap_title = m.group(2).strip() + " " + m.group(3).strip()
            chap_raw = f"第{han2num_to_str(i)}回 {chap_title}"
        else:
            m2 = TITLE_RE.search(text[:200])
            if m2:
                chap_raw = f"第{han2num_to_str(i)}回 {m2.group(2).strip()}"
                chap_title = m2.group(2).strip()

        chap_label = f"第{han2num_to_str(i)}回"
        chapter_id = f"{eid}/{i:03d}"
        page_id = f"{eid}#c{i:03d}"
        page_no = i

        paras = split_paragraphs(text)
        for li, para in enumerate(paras):
            line_id = f"{eid}#c{i:03d}#L{li:03d}"
            # 判断 form_type：标题行 / 悟元子评点 / 正文
            p = para.strip()
            if p.startswith("第") and "回" in p[:6]:
                ft = "title"
                is_com = False
            elif "悟元子曰" in p[:10]:
                ft = "commentary"
                is_com = True
            elif p.startswith("（悟元子"):
                ft = "commentary"
                is_com = True
            else:
                ft = "main"
                is_com = False
            lines.append(dict(
                line_id=line_id, page_id=page_id, edition=eid,
                page_no=page_no, line_idx=li,
                form_type=ft,
                text=p[:2000],
                char_count=len(p),
                confidence=0.85 if ft == "commentary" else 0.9,
                is_commentary=is_com,
            ))

        chapters.append(dict(
            chapter_id=chapter_id, edition=eid,
            chapter_label=chap_label,
            chapter_title=chap_title,
            raw_title=chap_raw,
            first_page=page_no,
            first_line_id=f"{eid}#c{i:03d}#L000",
        ))

        pages.append(dict(
            page_id=page_id, edition=eid,
            edition_dirname=eid, page_no=page_no, page_order=page_no,
            dc_source=f"{eid}\\c{i:03d}.txt",
            dc_title=f"{eid} 第{i}回" + (f" {chap_title}" if chap_title else ""),
            layout="text_from_wikisource",
            line_count=len(paras),
            char_count=sum(x["char_count"] for x in lines[-len(paras):]),
            main_line_count=sum(1 for x in lines[-len(paras):] if x["form_type"] == "main"),
            commentary_line_count=sum(1 for x in lines[-len(paras):] if x["is_commentary"]),
            entity_count=0, relation_count=0, event_count=0,
            chapter_ref=chap_label,
            model="wikisource-api", generated_at=now,
            ocr_seconds=0.0, annotation_seconds=0.0,
        ))
    return chapters, lines, pages


# ---------- 合并 & 落盘 ----------
def merge_and_write(old: pd.DataFrame, new_rows: list[dict], fname: str, key: str) -> pd.DataFrame:
    """按 key 合并，去重。返回合并后的 DataFrame。"""
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df_new[key] = df_new[key].astype(str)
        old[key] = old[key].astype(str)
        # 保留旧的所有列，补新列
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
    sys.stdout.reconfigure(encoding="utf-8")

    # 读旧数据
    ed_old = pd.read_parquet(BASE / "editions.parquet")
    ch_old = pd.read_parquet(BASE / "chapters.parquet")
    ln_old = pd.read_parquet(BASE / "lines.parquet")
    pg_old = pd.read_parquet(BASE / "pages.parquet")

    print(f"旧: editions={len(ed_old)} chapters={len(ch_old)} lines={len(ln_old)} pages={len(pg_old)}")

    # 抽
    ch1, ln1, pg1 = process_gubao()
    ch2, ln2, pg2 = process_baihui()
    print(f"新-古本: chapters={len(ch1)} lines={len(ln1)} pages={len(pg1)}")
    print(f"新-百回详注: chapters={len(ch2)} lines={len(ln2)} pages={len(pg2)}")

    # 合并 editions
    ed_new = pd.DataFrame(NEW_EDITIONS)
    ed = merge_and_write(ed_old, NEW_EDITIONS, "editions.parquet", "edition_id")

    # 合并 chapters / lines / pages
    ch = merge_and_write(ch_old, ch1 + ch2, "chapters.parquet", "chapter_id")
    ln = merge_and_write(ln_old, ln1 + ln2, "lines.parquet", "line_id")
    pg = merge_and_write(pg_old, pg1 + pg2, "pages.parquet", "page_id")

    print(f"合并后: editions={len(ed)} chapters={len(ch)} lines={len(ln)} pages={len(pg)}")

    # 写回 04_knowledge_data/ 和 docs/data/
    for name, df in [("editions", ed), ("chapters", ch), ("lines", ln), ("pages", pg)]:
        (BASE / f"{name}.parquet").parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(BASE / f"{name}.parquet", index=False)
        (DOCS / "data").mkdir(parents=True, exist_ok=True)
        df.to_parquet(DOCS / "data" / f"{name}.parquet", index=False)

    print("\n落盘完成：")
    for name in ["editions", "chapters", "lines", "pages"]:
        p = BASE / f"{name}.parquet"
        print(f"  {name}: {p.stat().st_size/1024:.1f} KB")

    # 校验
    print("\n按 edition 分布：")
    for f in ["chapters", "lines", "pages"]:
        df = pd.read_parquet(BASE / f"{f}.parquet")
        vc = df["edition"].value_counts().to_dict()
        print(f"  {f}: {vc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
