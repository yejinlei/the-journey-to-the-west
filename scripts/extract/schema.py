# -*- coding: utf-8 -*-
"""《西游记》本体双层 schema + VLM prompts。

形式层 (Form Layer)：OCR 分层 —— 章节、正文、评点、版本元数据
主题层 (Subject Layer)：实体/关系/事件 —— 人物、事件、地点、宗教、法宝等

输出：JSON-LD，可被 Protégé / Stardog / Neo4j (JSON-LD 导入) 消费。
"""
import uuid
from datetime import datetime, timezone

VERSION = "1.0.0"

NAMESPACES = {
    "@context": {
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dct": "http://purl.org/dc/terms/",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "bibo": "http://purl.org/vocab/bibo/",
        "prov": "http://www.w3.org/ns/prov#",
        "jtw": "http://xjy.ontology.local/",
    }
}

# ---------- 版本目录映射 ----------
EDITIONS = {
    "世德堂本":              ("shidetang",    "世德堂本（万历二十年金陵世德堂 1592）"),
    "杨闽斋本":              ("yangmizhai",   "杨闽斋本（天启四年 1624）"),
    "闽斋堂本":              ("mizhantang",   "闽斋堂本"),
    "李评本":                ("li_ping",      "李评本（明李廷机评点本）"),
    "李评本_Gallica4031":    ("li_ping",      "李评本（Gallica 分册 1）"),
    "李评本_Gallica4032":    ("li_ping",      "李评本（Gallica 分册 2）"),
    "李评本_Gallica4033":    ("li_ping",      "李评本（Gallica 分册 3）"),
    "李评本_Gallica4034":    ("li_ping",      "李评本（Gallica 分册 4）"),
    "李评本_Gallica4035":    ("li_ping",      "李评本（Gallica 分册 5）"),
    "新刻全像批评西游记":     ("xinke_pingbi", "新刻全像批评西游记（清）"),
    "大奇书本_Gallica4040":  ("daqishi",      "大奇书本（Gallica 分册 1）"),
    "大奇书本_Gallica4041":  ("daqishi",      "大奇书本（Gallica 分册 2）"),
    "大奇书本_Gallica4042":  ("daqishi",      "大奇书本（Gallica 分册 3）"),
    "大奇书本_Gallica4043":  ("daqishi",      "大奇书本（Gallica 分册 4）"),
    "真诠本":                ("zhenquan",     "真诠本（清陈士奇真诠本）"),
    "证道本":                ("zhengdao",     "证道本（明吴承恩证道本）"),
}

# ---------- 层级分类枚举 ----------
# Form Layer: 文本形态（评点位置体系）
FORM_TYPES = [
    "title",        # 回目
    "main",         # 正文
    "poem",         # 诗词
    "pre",          # 回前总评
    "post",         # 回后总评
    "inline",       # 夹批
    "top",          # 眉批（行外上方）
    "side",         # 旁批（行外侧边）
    "bottom",       # 底批
    "caption",      # 图注
    "colophon",     # 卷端题署/版署
    "preface",      # 序跋
]
FORM_TYPE_DESC = {
    "title":    "回目（第X回+题目）",
    "main":     "小说正文",
    "poem":     "诗词/赋",
    "pre":      "回前总评",
    "post":     "回后总评",
    "inline":   "夹批（嵌入正文行间小字）",
    "top":      "眉批（正文上方行外小字）",
    "side":     "旁批（正文侧边小字）",
    "bottom":   "底批（正文下方小字）",
    "caption":  "插图说明/图注",
    "colophon": "卷端题署/版署（书名作者刊刻信息）",
    "preface":  "序跋片段",
}

# Subject Layer: 主题实体类型
SUBJECT_TYPES = ["person", "event", "place", "religion", "artifact",
                 "monster", "official_title", "quote"]

# Subject Layer: 关系谓词（jtw:xxx）
RELATION_PREDICATES = [
    "jtw:isMasterOf", "jtw:isDiscipleOf", "jtw:isSiblingOf", "jtw:isTwinOf",
    "jtw:hasWeapon", "jtw:transformsTo", "jtw:travelsTo",
    "jtw:defeats", "jtw:fightsAgainst", "jtw:rescues",
    "jtw:worships", "jtw:commands", "jtw:alliedWith",
    "jtw:isKingOf", "jtw:residesIn",
]

# ---------- 页面级 URI & 元数据 ----------

def new_uri(prefix="page"):
    return f"http://xjy.ontology.local/{prefix}/{uuid.uuid4().hex[:12]}"


def page_uri(edition_code, page_no):
    return f"http://xjy.ontology.local/edition/{edition_code}/page/{page_no}"


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def page_record_meta(base_uri, source_rel, edition_code, edition_name, page_no, page_index):
    return {
        "@id": base_uri,
        "@type": ["bibo:Page", "jtw:BookPage"],
        "dc:title": f"{edition_name} 第{page_no}页",
        "dc:source": source_rel,
        "jtw:editionCode": edition_code,
        "jtw:editionName": edition_name,
        "jtw:pageNo": page_no,
        "jtw:pageOrderInEdition": page_index,
        "prov:wasGeneratedAt": now_iso(),
        "prov:usedTool": "sensenova-6.8-flash-lite",
    }


# ---------- VLM Prompts（精简以适配推理模型 token 预算） ----------

SYSTEM_OCR = (
    "你是《西游记》明清刻本 OCR，专长识别评点本。\n"
    "转录图中所有文字并分层，输出严格 JSON，第一字符 { 最后 }，禁止代码围栏。\n\n"
    "阅读顺序：竖排从右到左从上到下；横排从左到右从上到下。\n\n"
    "格式：\n"
    '{"layout":"vertical|horizontal|blank",'
    '"lines":[{"type":"<T>","text":"<转录>","conf":0.9}],'
    '"page_meta":{"has_illustration":false,"notes":"","line_count":0}}\n\n'
    "T 简写：title=回目 main=正文 poem=诗词 pre=回前总评 post=回后总评 "
    "inline=夹批 top=眉批 side=旁批 bottom=底批 caption=图注 colophon=题署 preface=序跋\n\n"
    "重点：\n"
    "- 页面上所有小字都要单独成 line，用对应评点类型；不要把评点混入 main\n"
    "- 眉批=正文上方行外小字；旁批=正文侧边小字；夹批=嵌入正文行间小字\n"
    "- 回目通常一行，位于正文上方，标 title\n"
    "- 保留繁体异体俗字；不添现代标点；每 line ≤400 字；忠于原字。"
)

SYSTEM_ANNOTATE = (
    "你是《西游记》本体抽取引擎。基于已分层文本抽实体/关系/事件，输出严格 JSON，第一字符 { 最后 }。\n\n"
    "实体类型：person 人物 | event 情节事件 | place 地点 | religion 宗教术语 | "
    "artifact 法宝兵器 | monster 妖怪 | official_title 官职称号 | quote 诗句经文\n\n"
    "关系谓词：jtw:isMasterOf isDiscipleOf isSiblingOf isTwinOf hasWeapon transformsTo "
    "travelsTo defeats fightsAgainst rescues worships commands alliedWith isKingOf residesIn\n\n"
    "格式：\n"
    '{"entities":[{"id":"<slug>","type":"<T>","label":"<原文名>","canonical_name":"<规范名>",'
    '"aliases":[],"mentions":[{"line_idx":0,"text":"<片段>"}],"attributes":{}}],'
    '"relationships":[{"subject_id":"<id>","predicate":"jtw:xxx","object":"<label 或 URI>",'
    '"evidence":"<片段>","line_idx":0}],'
    '"events":[{"name":"<事件>","actor_ids":[],"place_label":"","summary":"","lines":[]}],'
    '"chapter_ref":"第X回","confidence":0.9}\n\n'
    "规则：不编造无证据内容；line_idx 必须是 lines 数组真实下标；找不到实体时数组为空。"
)

USER_OCR = "分层转录此页所有文字，返回严格 JSON。"

USER_ANNOTATE = (
    "以下是该页 OCR 结果（JSON）。请按 schema 抽取实体/关系/事件，返回严格 JSON。\n"
    "{lines_json}"
)
