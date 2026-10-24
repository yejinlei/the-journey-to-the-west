/* ============================================================
   router.js —— 本地规则引擎：根据用户提问关键词路由到合适的工具
   未配置大模型时的兜底路径；LLM 调用失败时也可降级到此处。
   ============================================================ */

import { getTool } from './tools.js';

export const HELP_TEXT = [
  '### 你好，我是「西游记知识图谱 Agent」',
  '',
  '当前处于**本地规则引擎**模式（未配置大模型）。你可以试试以下自然语言提问：',
  '',
  '- 图谱总览 / 有哪些数据',
  '- 孙悟空 / 孫大聖 / 唐僧 / 白骨精（人物画像）',
  '- 谁和谁（人物共现，例："唐僧和孙悟空"）',
  '- 法宝（如意金箍棒、紧箍儿、芭蕉扇等）',
  '- 三教论理（佛/道/儒分布）',
  '- 诙谐谱（悟空耍猴调、唐僧念經）',
  '- 母题追踪（如"拜師"、"受戒"）',
  '- 版本比较',
  '',
  '若要启用自然语言多步推理，请到左侧「⚙️ 模型与 Key 设置」中配置 OpenAI 兼容接口（推荐 OpenRouter）。',
].join('\n');

/* 关键词 → 工具路由规则 */
const RULES = [
  {
    match: /图谱总览|总览|有多少|概况|规模|统计|多少页|多少章/,
    pick: () => ({ tool: '知识图谱总览', args: {} }),
  },
  {
    match: /版本(比较|差异|对比)|不同版本|版本清单/,
    pick: (q) => {
      const codes = (q.match(/[\w\-]+/g) || []).filter((x) => /^xinke|zhuyi|gao|jing|yuechao/i.test(x));
      return { tool: '版本比较', args: codes.length >= 2 ? { editionA: codes[0], editionB: codes[1] } : {} };
    },
  },
  {
    match: /第?[一二三四五六七八九十百]+回|回目|章节/,
    pick: (q) => {
      const m = q.match(/第?[一二三四五六七八九十百零\d]+回/);
      return { tool: '章节检索', args: m ? { chapter: m[0] } : {} };
    },
  },
  {
    match: /法宝|金箍棒|金箍|紧箍|芭蕉扇|紫金葫芦|定海神针|如意/,
    pick: (q) => {
      const kw = q.match(/金箍棒|金箍|紧箍|芭蕉扇|紫金葫芦|定海神针|如意/) || [];
      return { tool: '法宝查询', args: kw[0] ? { keyword: kw[0] } : {} };
    },
  },
  {
    match: /三教|佛教|道教|儒教|释|佛道|论理|三家|张书绅|杨义/,
    pick: () => ({ tool: '三教论理分析', args: {} }),
  },
  {
    match: /诙谐|耍猴|呆子|阿弥陀佛|念经|插科打诨|俏皮/,
    pick: (q) => {
      if (/呆子|耍猴|呆驢/.test(q)) return { tool: '诙谐点查找', args: { witType: 'monkey_mischief' } };
      if (/阿彌陀佛|阿弥陀佛|善哉|念经|經雲/.test(q)) return { tool: '诙谐点查找', args: { witType: 'tang_sutra' } };
      if (/買賣|銀子|市價|鋪/.test(q)) return { tool: '诙谐点查找', args: { witType: 'market' } };
      return { tool: '诙谐点查找', args: {} };
    },
  },
  {
    match: /语体|口吻|体例|文白/,
    pick: () => ({ tool: '语体分析', args: {} }),
  },
  {
    match: /母题|motif|拜師|受戒|變化|變化|结拜|受封|打怪|取经/,
    pick: (q) => {
      const kws = ['拜師', '拜师', '受戒', '變化', '变化', '结拜', '受封', '打怪', '取经', '入道'];
      const found = kws.find((k) => q.includes(k));
      return { tool: '母题追踪', args: { motif: found || '拜師' } };
    },
  },
  {
    match: /共现|和.*一起|和.*同行|谁和谁|和.*的关系/,
    pick: (q) => {
      // 提取两个人名
      const names = extractNames(q);
      if (names.length >= 2) return { tool: '人物共现', args: { personA: names[0], personB: names[1] } };
      return { tool: '人物共现', args: { personA: '孫行者', personB: '唐僧' } };
    },
  },
  {
    match: /关系|谁拜|拜誰|師徒|弟子|师徒|isDiscipleOf/,
    pick: (q) => {
      const names = extractNames(q);
      return { tool: '关系链查询', args: names[0] ? { person: names[0] } : {} };
    },
  },
  {
    match: /事件|情节|故事|战妖|降妖|取经/,
    pick: (q) => {
      const kwMatch = q.match(/(战妖|降妖|取经|求取|大闹|大闹天宫|收徒|拜師|受戒)/);
      return { tool: '事件检索', args: kwMatch ? { keyword: kwMatch[1] } : {} };
    },
  },
];

/* 主要人物关键词表（用于识别单人名） */
const PERSON_KEYWORDS = [
  '孙悟空', '孫悟空', '孫大聖', '孙行者', '孫行者', '齐天大圣', '行者', '悟空',
  '唐僧', '唐三藏', '三藏', '三藏法師',
  '八戒', '豬八戒', '猪八戒',
  '沙僧', '沙和尚', '沙悟淨', '悟淨',
  '白骨精', '白骨夫人', '白骨',
  '觀音', '观音', '觀音菩薩',
  '玉皇大天尊', '玉帝', '玉皇',
  '太上老君', '老君',
  '菩提祖師', '菩提', '師父',
  '金剛', '金公',
];

function extractNames(q) {
  const found = [];
  for (const n of PERSON_KEYWORDS) {
    if (q.includes(n) && !found.includes(n)) found.push(n);
    if (found.length >= 2) break;
  }
  return found;
}

/** 单人画像路由（作为最外层规则） */
function tryPersonProfile(q) {
  const names = extractNames(q);
  if (names.length === 1) return { tool: '人物画像', args: { person: names[0] } };
  return null;
}

/**
 * 主路由：返回 { tool, args, reason } 或 null
 */
export async function route(question) {
  const q = String(question || '').trim();
  if (!q) return null;

  // 尝试顺序：明确规则 → 单人画像
  for (const rule of RULES) {
    if (rule.match.test(q)) {
      try {
        const pick = rule.pick(q);
        if (pick && getTool(pick.tool)) return { ...pick, reason: rule.match.source };
      } catch (_) {}
    }
  }
  const profile = tryPersonProfile(q);
  if (profile && getTool(profile.tool)) return { ...profile, reason: 'person_profile' };

  return null;
}

/** 直接执行规则引擎一次 */
export async function runRoute(question) {
  const r = await route(question);
  if (!r) return { result: { text: HELP_TEXT, blocks: [] } };
  const tool = getTool(r.tool);
  if (!tool) return { result: { text: HELP_TEXT, blocks: [] } };
  try {
    const out = await tool.run(r.args || {});
    return { result: out, route: r };
  } catch (e) {
    return { result: { text: `规则引擎执行出错：${e.message}`, blocks: [] }, route: r };
  }
}
