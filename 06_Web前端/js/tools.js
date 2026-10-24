/* ============================================================
   tools.js —— 西游记知识图谱 · 白名单 SQL 查询工具集
   每个工具既可供本地规则引擎直接调用，也可作为 LLM function tool。

   12 个工具：
   1. 知识图谱总览      — overview
   2. 版本比较          — compare_versions
   3. 章节检索          — find_chapter
   4. 人物画像          — trace_person
   5. 人物共现          — find_coevolve
   6. 关系链查询        — trace_relationship
   7. 事件检索          — find_event
   8. 法宝/物件查询     — find_artifact
   9. 母题追踪          — find_motif
   10. 三教论理分析      — analyze_doctrine
   11. 语体/口吻分析    — analyze_register
   12. 诙谐点查找       — find_wit
   ============================================================ */

import { query, scalar } from './db.js';

/* --------- 缓存核心数据（人物、章节、关系） --------- */
let ENTITIES = null;
let CHAPTERS = null;
let EDGES = null;
let NAME_IDX = null;

/** 人物别名映射（西游常用简称） */
const ALIAS = {
  '孙悟空': 'sun-wukong', '孫悟空': 'sun-wukong', '孫大聖': 'sun-wukong',
  '孫行者': 'sun-wukong', '行者': 'sun-wukong', '齐天大圣': 'sun-wukong',
  '八戒': 'zhu-bajie', '豬八戒': 'zhu-bajie',
  '沙僧': 'sha-wujing', '沙和尚': 'sha-wujing', '孫沙悟淨': 'sha-wujing',
  '三藏': 'tang-sanzang', '唐僧': 'tang-sanzang', '唐三藏': 'tang-sanzang',
  '金剛': 'jin-gang', '金公': 'jin-gang', '唐僧徒': 'jin-gang',
  '白骨精': 'bai-gu-jing', '白骨夫人': 'bai-gu-jing', '白骨': 'bai-gu-jing',
};

function normKey(s) {
  return String(s == null ? '' : s).toLowerCase().replace(/[\s·.．・\-—_()（）]/g, '');
}

async function loadCore() {
  if (ENTITIES) return;
  const er = await query('SELECT * FROM entities');
  ENTITIES = er.rows;
  NAME_IDX = new Map();
  for (const e of ENTITIES) {
    for (const key of [normKey(e.label), normKey(e.canonical_name), normKey(e.entity_id_raw)]) {
      if (!key) continue;
      if (!NAME_IDX.has(key)) NAME_IDX.set(key, []);
      NAME_IDX.get(key).push(e.entity_id_raw);
    }
    if (e.aliases) {
      for (const a of String(e.aliases).split('|')) {
        const k = normKey(a);
        if (!k) continue;
        if (!NAME_IDX.has(k)) NAME_IDX.set(k, []);
        if (!NAME_IDX.get(k).includes(e.entity_id_raw)) NAME_IDX.get(k).push(e.entity_id_raw);
      }
    }
  }
  const cr = await query('SELECT * FROM chapters');
  CHAPTERS = cr.rows;
  const rr = await query('SELECT * FROM relationships');
  EDGES = rr.rows;
}

async function resolveEntity(name) {
  await loadCore();
  const raw = String(name == null ? '' : name).trim();
  if (!raw) return null;
  const k = normKey(raw);
  if (ALIAS[k]) return ALIAS[k];
  if (NAME_IDX.has(k)) {
    const arr = NAME_IDX.get(k);
    if (arr.length) return arr[0];
  }
  // 子串匹配
  const esc = raw.replace(/'/g, "''");
  const r = await query(`SELECT entity_id_raw FROM entities WHERE label LIKE '%${esc}%' OR canonical_name LIKE '%${esc}%' OR aliases LIKE '%${esc}%'`);
  return r.rows.length ? r.rows[0].entity_id_raw : null;
}

const esc = (s) => String(s == null ? '' : s).replace(/'/g, "''");

/* ============================================================
   工具定义
   ============================================================ */
export const TOOLS = [

  /* 1. 知识图谱总览 */
  {
    name: '知识图谱总览',
    label: '图谱总览',
    description: '返回西游记知识图谱的整体规模：版本数、页数、实体数、关系数、事件数、章节数等。',
    parameters: { type: 'object', properties: {} },
    async run() {
      const g = async (sql) => Number(await scalar(sql)) || 0;
      const editions = await g('SELECT count(*) FROM editions');
      const pages = await g('SELECT count(*) FROM pages');
      const lines = await g('SELECT count(*) FROM lines');
      const entities = await g('SELECT count(*) FROM entities');
      const relationships = await g('SELECT count(*) FROM relationships');
      const events = await g('SELECT count(*) FROM events');
      const mentions = await g('SELECT count(*) FROM mentions');
      const chapters = await g('SELECT count(*) FROM chapters');
      const annotations = await g('SELECT count(*) FROM annotations');

      const editionDist = await query(`SELECT edition, count(*) AS pages FROM pages GROUP BY edition ORDER BY pages DESC`);
      const typeDist = await query(`SELECT type, count(*) AS cnt FROM entities GROUP BY type ORDER BY cnt DESC`);
      const predDist = await query(`SELECT predicate, count(*) AS cnt FROM relationships GROUP BY predicate ORDER BY cnt DESC`);

      const lines_md = [
        '### 西游记知识图谱 · 总览',
        `- **版本数**：${editions}`,
        `- **页数**：${pages}｜**行级文本**：${lines}`,
        `- **实体**：${entities}｜**关系**：${relationships}｜**事件**：${events}`,
        `- **章节**：${chapters}｜**评点/注释**：${annotations}`,
        `- **共现提及**：${mentions}`,
        '',
        '**实体类型分布**：' + (typeDist.rows.length ? typeDist.rows.map((x) => `${x.type} ${x.cnt}`).join('｜') : '—'),
        '',
        '**关系谓词 Top**：' + (predDist.rows.length ? predDist.rows.map((x) => `${x.predicate} ${x.cnt}`).join('｜') : '—'),
      ];
      return {
        text: lines_md.join('\n'),
        blocks: [
          { type: 'table', title: '版本分布', columns: ['版本', '页数'], rows: editionDist.rows.map((x) => [x.edition, x.pages]) },
          { type: 'table', title: '实体类型', columns: ['类型', '数量'], rows: typeDist.rows.map((x) => [x.type, x.cnt]) },
        ],
        payload: { editions, pages, entities, relationships, events, chapters },
      };
    },
  },

  /* 2. 版本比较 */
  {
    name: '版本比较',
    label: '版本比较',
    description: '对比不同版本的页数、章节分布、实体出现差异。可指定两个版本，或查看全部版本对比。',
    parameters: {
      type: 'object',
      properties: {
        editionA: { type: 'string', description: '版本 A 的 code，如 xinke_pingbi' },
        editionB: { type: 'string', description: '版本 B 的 code' },
      },
    },
    async run(args) {
      const a = String(args.editionA || '').trim();
      const b = String(args.editionB || '').trim();
      const editions = await query('SELECT * FROM editions');
      const rows = editions.rows;

      if (!a && !b) {
        const dist = await query(`SELECT edition, count(*) AS pages, count(DISTINCT chapter_ref) AS chapters FROM pages GROUP BY edition ORDER BY pages DESC`);
        const entByEdition = await query(`SELECT edition, count(*) AS entities FROM entities GROUP BY edition ORDER BY entities DESC`);
        const entMap = Object.fromEntries(entByEdition.rows.map((x) => [x.edition, x.entities]));
        return {
          text: '### 版本总览\n' + rows.map((x) => `- **${x.edition_name || x.edition_code}**（${x.edition_code}）：${x.year || '?'} 年｜${x.publisher || ''}｜${x.note || ''}`).join('\n') +
            '\n\n**已抽取统计**：' + dist.rows.map((x) => `${x.edition}：${x.pages} 页 / ${x.chapters} 章 / ${entMap[x.edition] || 0} 实体`).join('；'),
          blocks: [{ type: 'table', title: '版本清单', columns: ['版本 code', '名称', '年代', '出版', '页数', '章节', '实体'], rows: rows.map((x) => [x.edition_code, x.edition_name, x.year || '—', x.publisher || '', (dist.rows.find((d) => d.edition === x.edition_code) || {}).pages || 0, (dist.rows.find((d) => d.edition === x.edition_code) || {}).chapters || 0, entMap[x.edition_code] || 0]) }],
          payload: { editions: rows },
        };
      }

      const codes = [a, b].filter(Boolean);
      const where = codes.length === 1 ? `edition = '${esc(codes[0])}'` : `edition IN ('${esc(codes[0])}','${esc(codes[1]||'')}' )`;
      const dist = await query(`SELECT edition, count(*) AS pages, count(DISTINCT chapter_ref) AS chapters FROM pages WHERE ${where} GROUP BY edition`);
      const entByEdition = await query(`SELECT edition, count(*) AS entities FROM entities WHERE ${where} GROUP BY edition`);
      const relByEdition = await query(`SELECT edition, count(*) AS relationships FROM relationships WHERE ${where} GROUP BY edition`);
      const entByType = await query(`SELECT edition, type, count(*) AS cnt FROM entities WHERE ${where} GROUP BY edition, type ORDER BY edition, cnt DESC`);
      const lineStats = await query(`SELECT edition, avg(line_count) AS avg_lines, sum(char_count) AS total_chars FROM pages WHERE ${where} AND line_count > 0 GROUP BY edition`);

      return {
        text: '### 版本比较\n' + dist.rows.map((x) => `- **${x.edition}**：${x.pages} 页 / ${x.chapters} 章 / 实体 ${entByEdition.rows.find((e) => e.edition === x.edition)?.entities || 0} / 关系 ${relByEdition.rows.find((e) => e.edition === x.edition)?.relationships || 0}`).join('\n') +
          '\n\n**实体类型分布**：\n' + entByType.rows.map((x) => `- ${x.edition} · ${x.type}：${x.cnt}`).join('\n'),
        blocks: [{ type: 'table', title: '版本指标', columns: ['版本', '页数', '章节', '实体', '关系', '平均每页行数', '总字数'], rows: dist.rows.map((x) => { const st = lineStats.rows.find((s) => s.edition === x.edition); return [x.edition, x.pages, x.chapters, entByEdition.rows.find((e) => e.edition === x.edition)?.entities || 0, relByEdition.rows.find((e) => e.edition === x.edition)?.relationships || 0, st ? Number(st.avg_lines).toFixed(1) : '—', st ? Number(st.total_chars).toLocaleString() : '—']; }) }],
        payload: { editions: codes, dist: dist.rows },
      };
    },
  },

  /* 3. 章节检索 */
  {
    name: '章节检索',
    label: '章节检索',
    description: '查询回目信息。给回号（如"第八十六回"）返回对应章节详情；不给则列出所有章节。',
    parameters: {
      type: 'object',
      properties: {
        chapter: { type: 'string', description: '回目，如"第八十六回"、"水母助威"' },
      },
    },
    async run(args) {
      await loadCore();
      const kw = String(args.chapter || '').trim();
      if (!kw) {
        return {
          text: `### 章节列表（${CHAPTERS.length} 条）\n` + CHAPTERS.map((x) => `- **${x.chapter_label}**｜${x.chapter_title || ''}｜首页 p${x.first_page}`).join('\n'),
          blocks: [{ type: 'table', title: '章节', columns: ['版本', '回目', '回目题', '首页'], rows: CHAPTERS.map((x) => [x.edition, x.chapter_label, x.chapter_title || '', x.first_page]) }],
          payload: { chapters: CHAPTERS },
        };
      }
      const escKw = esc(kw);
      const matched = CHAPTERS.filter((x) => x.chapter_label.includes(kw) || (x.chapter_title || '').includes(kw));
      if (!matched.length) return { text: `未找到「${kw}」相关章节。`, payload: { error: 'not_found' } };
      // 取对应页文本
      const pages = matched.flatMap((c) => {
        return [{ edition: c.edition, chapter: c.chapter_label, chapter_title: c.chapter_title || '', first_page: c.first_page, lines: '' }];
      });
      return {
        text: '### 章节检索：' + kw + '\n' + matched.map((x) => `#### ${x.chapter_label} ${x.chapter_title || ''}\n版本：${x.edition}｜首页：p${x.first_page}`).join('\n\n'),
        blocks: [{ type: 'table', title: '章节', columns: ['版本', '回目', '回目题', '首页'], rows: matched.map((x) => [x.edition, x.chapter_label, x.chapter_title || '', x.first_page]) }],
        payload: { chapters: matched },
      };
    },
  },

  /* 4. 人物画像 */
  {
    name: '人物画像',
    label: '人物画像',
    description: '查询人物完整档案：别名、类型、共现关系、参与事件。',
    parameters: {
      type: 'object',
      properties: { person: { type: 'string', description: '人物名，如"孙悟空"、"唐僧"、"白骨精"、"豬八戒"、"沙和尚"' } },
      required: ['person'],
    },
    async run(args) {
      await loadCore();
      const id = await resolveEntity(args.person);
      if (!id) return { text: `未找到「${args.person}」。可试：孫悟空/孫大聖/行者/唐僧/八戒/沙和尚/白骨精`, payload: { error: 'not_found' } };
      const ent = ENTITIES.find((e) => e.entity_id_raw === id);
      const lines = [
        `### ${ent ? (ent.canonical_name || ent.label) : id}`,
        ent && ent.label ? `- **原文名**：${ent.label}` : '',
        ent && ent.canonical_name ? `- **规范名**：${ent.canonical_name}` : '',
        ent && ent.aliases ? `- **别名**：${ent.aliases}` : '',
        `- **类型**：${ent ? ent.type : '?'}`,
        `- **出现次数**：${ent ? ent.mention_count : '?'} 次`,
      ].filter(Boolean).join('\n');

      // 相关关系
      const rel = EDGES.filter((e) => e.subject_id === id || e.object_id === id);
      if (rel.length) {
        lines += '\n\n**关系**（' + rel.length + ' 条）：';
        rel.forEach((r) => {
          const other = r.subject_id === id ? r.object_id : r.subject_id;
          lines += `\n- ${r.subject_id === id ? '→ ' : '← '} ${r.predicate.replace('jtw:', '')} → **${other}**（${r.evidence || ''}）`;
        });
      }

      // 参与事件
      const ev = await query(`SELECT * FROM events WHERE actor_ids LIKE '%${esc(id)}%'`);
      if (ev.rows.length) {
        lines += '\n\n**参与事件**：';
        ev.rows.forEach((e) => lines += `\n- ${e.name}｜${e.summary || ''}`);
      }

      return {
        text: lines,
        blocks: [
          rel.length ? { type: 'table', title: '关系', columns: ['方向', '谓词', '对象', '证据'], rows: rel.map((r) => [r.subject_id === id ? '→' : '←', r.predicate, r.subject_id === id ? r.object_id : r.subject_id, r.evidence || '']) } : null,
        ].filter(Boolean),
        payload: { entity: ent, relations: rel, events: ev.rows },
      };
    },
  },

  /* 5. 人物共现 */
  {
    name: '人物共现',
    label: '共现分析',
    description: '查询两位人物在同一页/同一事件中的共现情况。',
    parameters: {
      type: 'object',
      properties: {
        personA: { type: 'string' },
        personB: { type: 'string' },
      },
      required: ['personA', 'personB'],
    },
    async run(args) {
      const a = await resolveEntity(args.personA);
      const b = await resolveEntity(args.personB);
      if (!a || !b) return { text: `未找到 ${!a ? args.personA : args.personB}。`, payload: { error: 'not_found' } };
      const rel = EDGES.filter((e) =>
        (e.subject_id === a && e.object_id === b) ||
        (e.subject_id === b && e.object_id === a));
      // 事件共现
      const evA = await query(`SELECT * FROM events WHERE actor_ids LIKE '%${esc(a)}%'`);
      const evB = await query(`SELECT * FROM events WHERE actor_ids LIKE '%${esc(b)}%'`);
      const shared = evA.rows.filter((x) => x.event_id === evB.rows.find((y) => y.event_id === x.event_id)?.event_id);
      const lines = [
        `### 共现：${a} × ${b}`,
        `- **直接关系**：${rel.length} 条`,
        `- **共同事件**：${shared.length} 个`,
      ];
      if (rel.length) {
        lines.push('\n**关系**：');
        rel.forEach((r) => lines.push(`- ${r.subject_id} → ${r.predicate.replace('jtw:','')} → ${r.object_id}`));
      }
      if (shared.length) {
        lines.push('\n**共同事件**：');
        shared.forEach((e) => lines.push(`- ${e.name}｜${e.summary || ''}`));
      }
      return {
        text: lines.join('\n'),
        payload: { a, b, rel: rel.length, shared: shared.length },
      };
    },
  },

  /* 6. 关系链查询 */
  {
    name: '关系链查询',
    label: '关系链',
    description: '查询某人物的关系链（谁拜他/他拜谁/他打谁），或按关系类型（如 isDiscipleOf）过滤。',
    parameters: {
      type: 'object',
      properties: {
        person: { type: 'string', description: '人物名（可选）' },
        predicate: { type: 'string', description: '关系谓词，如 isDiscipleOf（不带 jtw:）' },
        direction: { type: 'string', description: '出/入/双向（默认双向）' },
      },
    },
    async run(args) {
      await loadCore();
      let edges = EDGES;
      if (args.person) {
        const id = await resolveEntity(args.person);
        if (!id) return { text: `未找到「${args.person}」。`, payload: { error: 'not_found' } };
        const d = args.direction || '双向';
        edges = edges.filter((e) => d === '出' ? e.subject_id === id : d === '入' ? e.object_id === id : (e.subject_id === id || e.object_id === id));
      }
      if (args.predicate) {
        const p = 'jtw:' + args.predicate.replace(/^jtw:/, '');
        edges = edges.filter((e) => e.predicate === p);
      }
      if (!edges.length) return { text: '未找到匹配的关系。', payload: { edges: [] } };
      return {
        text: `### 关系链（${edges.length} 条）\n` + edges.map((e) => `- ${e.subject_id} —${e.predicate.replace('jtw:','')}→ ${e.object_id}\n  证据：${e.evidence || ''}`).join('\n'),
        blocks: [{ type: 'table', title: '关系', columns: ['主体', '谓词', '客体', '证据', '页'], rows: edges.map((e) => [e.subject_id, e.predicate.replace('jtw:',''), e.object_id, e.evidence || '', e.page_id || '']) }],
        payload: { edges },
      };
    },
  },

  /* 7. 事件检索 */
  {
    name: '事件检索',
    label: '事件检索',
    description: '查询事件/情节。可按关键词、演员（人物）、地点过滤。',
    parameters: {
      type: 'object',
      properties: {
        keyword: { type: 'string', description: '关键词，如"寻师父"、"战妖"' },
        actor: { type: 'string', description: '参与人物，如"孙行者"' },
      },
    },
    async run(args) {
      const kw = String(args.keyword || '').trim();
      const actor = String(args.actor || '').trim();
      const conditions = [];
      if (kw) conditions.push(`(name LIKE '%${esc(kw)}%' OR summary LIKE '%${esc(kw)}%')`);
      if (actor) conditions.push(`actor_ids LIKE '%${esc(actor)}%'`);
      const where = conditions.length ? ' WHERE ' + conditions.join(' AND ') : '';
      const r = await query(`SELECT * FROM events${where} ORDER BY page_no`);
      if (!r.rows.length) return { text: `未找到匹配的事件。`, payload: { events: [] } };
      return {
        text: `### 事件（${r.rows.length} 条）\n` + r.rows.map((x) => `#### ${x.name}\n**演员**：${x.actor_ids || ''}｜**地点**：${x.place_label || '—'}｜**页**：${x.page_id}\n> ${x.summary || ''}`).join('\n\n'),
        blocks: [{ type: 'table', title: '事件清单', columns: ['事件', '演员', '地点', '页', '摘要'], rows: r.rows.map((x) => [x.name, x.actor_ids || '', x.place_label || '', x.page_id, x.summary || '']) }],
        payload: { events: r.rows },
      };
    },
  },

  /* 8. 法宝/物件查询 */
  {
    name: '法宝查询',
    label: '法宝查询',
    description: '查询法宝/兵器/法器类实体及其持有关系。当前从 entities 表 type=artifact 中检索。',
    parameters: {
      type: 'object',
      properties: { keyword: { type: 'string', description: '法宝名或关键词，如"如意金箍棒"、"紧箍儿"、"芭蕉扇"' } },
    },
    async run(args) {
      const kw = String(args.keyword || '').trim();
      const where = kw ? ` AND (label LIKE '%${esc(kw)}%' OR canonical_name LIKE '%${esc(kw)}%' OR aliases LIKE '%${esc(kw)}%')` : '';
      const r = await query(`SELECT * FROM entities WHERE type='artifact'${where} ORDER BY label`);
      if (!r.rows.length) return { text: kw ? `未找到法宝「${kw}」。` : '法宝表暂无数据（VLM 抽取时会识别到 type=artifact）。', payload: { artifacts: [] } };
      return {
        text: `### 法宝（${r.rows.length} 个）\n` + r.rows.map((x) => `- **${x.label}**（${x.canonical_name || ''}｜别名：${x.aliases || ''}）｜出现 ${x.mention_count} 次`).join('\n'),
        blocks: [{ type: 'table', title: '法宝', columns: ['原名', '规范名', '别名', '出现次数'], rows: r.rows.map((x) => [x.label, x.canonical_name || '', x.aliases || '', x.mention_count]) }],
        payload: { artifacts: r.rows },
      };
    },
  },

  /* 9. 母题追踪 */
  {
    name: '母题追踪',
    label: '母题追踪',
    description: '在正文行级文本中搜索母题关键词（打怪/拜师/受封/变化/结拜/受戒等），返回出现位置。',
    parameters: {
      type: 'object',
      properties: {
        motif: { type: 'string', description: '母题关键词，如"拜師"、"受戒"、"變化"、"打怪"' },
        edition: { type: 'string', description: '版本 code（可选）' },
      },
      required: ['motif'],
    },
    async run(args) {
      const kw = String(args.motif || '').trim();
      const edition = String(args.edition || '').trim();
      if (!kw) return { text: '必须指定 motif 关键词。', payload: { error: 'missing' } };
      const escKw = esc(kw);
      const editionWhere = edition ? ` AND edition='${esc(edition)}'` : '';
      const r = await query(`SELECT line_id, edition, page_no, text FROM lines WHERE text LIKE '%${escKw}%'${editionWhere} ORDER BY page_no LIMIT 50`);
      if (!r.rows.length) return { text: `未找到包含「${kw}」的行文本。`, payload: { lines: [] } };
      return {
        text: `### 母题「${kw}」在 ${r.rows.length} 行中出现\n` + r.rows.map((x) => `- **${x.page_id || x.line_id}** · p${x.page_no}：${(x.text || '').slice(0, 80)}`).join('\n'),
        blocks: [{ type: 'table', title: '匹配行', columns: ['版本', '页', '行ID', '原文片段'], rows: r.rows.map((x) => [x.edition, x.page_no, x.line_id, (x.text || '').slice(0, 120)]) }],
        payload: { motif: kw, matches: r.rows.length },
      };
    },
  },

  /* 10. 三教论理分析 */
  {
    name: '三教论理分析',
    label: '三教论理',
    description: '分析儒释道三教在正文中的分布（关键词命中）：佛教（佛/僧/佛經/菩薩）、道教（道/玄/丹/三清/太上）、儒教（儒/聖人/孔/孟）。',
    parameters: {
      type: 'object',
      properties: {
        edition: { type: 'string', description: '版本 code（可选）' },
      },
    },
    async run(args) {
      const edition = String(args.edition || '').trim();
      const where = edition ? ` AND edition='${esc(edition)}'` : '';
      const terms = {
        '佛教（佛）': ['佛', '菩薩', '彌勒', '金剛', '禪', '僧'],
        '道教（道）': ['道', '三清', '太上', '丹', '玄', '天尊', '仙'],
        '儒教（儒）': ['儒', '聖人', '孔子', '孟', '仁', '禮'],
      };
      const stats = {};
      for (const [label, kws] of Object.entries(terms)) {
        let total = 0;
        for (const k of kws) {
          const r = await scalar(`SELECT count(*) FROM lines WHERE text LIKE '%${esc(k)}%'${where}`);
          total += Number(r || 0);
        }
        stats[label] = total;
      }
      return {
        text: `### 三教关键词分布${edition ? `（${edition}）` : '（全版本）'}\n` + Object.entries(stats).map(([k, v]) => `- **${k}**：命中 ${v} 行`).join('\n') +
          '\n\n> 依据张书绅《西游记通解》三教合一论、杨义"三教归一是作者基本思路"研究。数字仅供倾向参考，需结合上下文判断褒贬。',
        blocks: [{ type: 'bar', title: '三教关键词命中行数', data: Object.entries(stats).map(([k, v]) => ({ label: k, value: v })) }],
        payload: { stats, edition: edition || null },
      };
    },
  },

  /* 11. 语体/口吻分析 */
  {
    name: '语体分析',
    label: '语体分析',
    description: '分析文本行级类型的分布（title/main/poem/评点等），反映版本体例差异。',
    parameters: {
      type: 'object',
      properties: {
        edition: { type: 'string' },
      },
    },
    async run(args) {
      const edition = String(args.edition || '').trim();
      const where = edition ? ` AND edition='${esc(edition)}'` : '';
      const r = await query(`SELECT type, count(*) AS cnt FROM lines WHERE 1=1${where} GROUP BY type ORDER BY cnt DESC`);
      if (!r.rows.length) return { text: '暂无语体分布数据。', payload: { types: [] } };
      return {
        text: `### 语体分布${edition ? `（${edition}）` : '（全版本）'}\n` + r.rows.map((x) => `- **${x.type}**：${x.cnt} 行`).join('\n') +
          '\n\n> 参考 fytj 红楼字镜思路：title/main/poem/pre/post/inline/top/side/bottom 等，用于跨版本对齐。',
        blocks: [{ type: 'bar', title: '语体行数', data: r.rows.map((x) => ({ label: x.type, value: Number(x.cnt) })) }],
        payload: { types: r.rows },
      };
    },
  },

  /* 12. 诙谐点查找 */
  {
    name: '诙谐点查找',
    label: '诙谐谱',
    description: '在文本中查找诙谐点：悟空耍猴调（"這呆子"、"呆子"、"呆驢"、"呆小妖"）、唐僧念經語（"阿弥陀佛"、"善哉"）、市井插科打诨等。',
    parameters: {
      type: 'object',
      properties: {
        witType: { type: 'string', description: '诙谐类型：monkey_mischief / tang_sutra / market / demon_quip / all' },
        keyword: { type: 'string', description: '关键词，如"呆子"、"阿弥陀佛"' },
      },
    },
    async run(args) {
      const wt = String(args.witType || 'all');
      const kw = String(args.keyword || '').trim();
      const typePatterns = {
        'monkey_mischief': ['呆子', '呆驢', '呆小妖', '這呆子', '呆賊', '無賴'],
        'tang_sutra': ['阿彌陀佛', '阿弥陀佛', '善哉', '經雲', '佛祖'],
        'market': ['買賣', '銀子', '一文', '市價', '貨', '鋪'],
        'demon_quip': ['妖言', '妖怪道', '妖道', '小妖'],
      };
      const useKw = kw || (wt !== 'all' && typePatterns[wt]) ? (kw ? [kw] : typePatterns[wt]) : [];
      if (!useKw.length) {
        const allHits = [];
        for (const kws of Object.values(typePatterns)) {
          for (const k of kws) {
            const r = await query(`SELECT line_id, page_no, text FROM lines WHERE text LIKE '%${esc(k)}%' LIMIT 20`);
            r.rows.forEach((x) => allHits.push({ keyword: k, ...x }));
          }
        }
        return {
          text: `### 诙谐谱（默认模式，扫描全部类型）\n共 ${allHits.length} 处命中：\n` + allHits.slice(0, 30).map((x) => `- **[${x.keyword}]** p${x.page_no}：${(x.text || '').slice(0, 60)}`).join('\n'),
          blocks: [{ type: 'table', title: '诙谐点', columns: ['关键词', '页', '原文'], rows: allHits.slice(0, 40).map((x) => [x.keyword, x.page_no, (x.text || '').slice(0, 100)]) }],
          payload: { hits: allHits.length },
        };
      }
      const hits = [];
      for (const k of useKw) {
        const r = await query(`SELECT line_id, page_no, text FROM lines WHERE text LIKE '%${esc(k)}%' LIMIT 30`);
        r.rows.forEach((x) => hits.push({ keyword: k, ...x }));
      }
      if (!hits.length) return { text: `未找到「${useKw.join('/')}」相关诙谐点。`, payload: { hits: [] } };
      return {
        text: `### 诙谐谱 · ${wt}（${hits.length} 处）\n` + hits.map((x) => `- **[${x.keyword}]** p${x.page_no}：${(x.text || '').slice(0, 80)}`).join('\n'),
        blocks: [{ type: 'table', title: '诙谐点', columns: ['关键词', '页', '原文'], rows: hits.map((x) => [x.keyword, x.page_no, (x.text || '').slice(0, 120)]) }],
        payload: { hits },
      };
    },
  },
];

export function getTool(name) {
  return TOOLS.find((t) => t.name === name) || null;
}

export function toolsForLLM() {
  return TOOLS.map((t) => ({
    type: 'function',
    function: { name: t.name, description: t.description, parameters: t.parameters || { type: 'object', properties: {} } },
  }));
}
