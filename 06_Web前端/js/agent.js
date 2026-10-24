/* ============================================================
   agent.js —— 基于 LangGraph.js 的西游记知识图谱 Agent
   状态图：plan → act ↔ plan → compose
   双模式：
     · LLM 模式：大模型自主决定调用哪些工具，最后综合成文
     · 规则模式：未配置大模型时，本地规则引擎选定工具直接输出
   ============================================================ */

import { StateGraph, Annotation, START, END } from '../lib/duckdb/langgraph.bundle.js';
import { toolsForLLM, getTool } from './tools.js';
import { runRoute, route, HELP_TEXT } from './router.js';
import { loadConfig, hasLLM, normalizeBaseUrl, mixedContentWarning } from './config.js';

const MAX_TOOL_ROUNDS = 4;

/* ------------------------- 系统提示词 ------------------------- */

const SYSTEM_PROMPT = `你是「西游记知识图谱 Agent」的查询助手。你的知识来自一个本地知识图谱（DuckDB 中存储的本体论数据），必须通过提供的工具获取事实，不得凭记忆编造。

【本体覆盖范围】
- 版本：新刻全像批評西遊記（明刊）、清平堂本、芥子園本、世德堂本、朱熹評本、楊慎本、袁于令評本、劉文龍評本
- 表结构：editions（版本）、pages（页）、lines（行级文本）、chapters（回目）、entities（实体：人物/事件/物件/道場/評点/学者论争）、relationships（关系）、events（事件）、mentions（共现）、annotations（评点）
- 特色表：discipleship（拜师/授经）、antagonism（敌对）、kinship（血缘/亲属）、possession（法宝持有）、membership（隶属）、involvement（事件参与）、scholar_arguments（学者论争）
- 隐性层：三教论理（佛/道/儒）、语体（title/main/poem/pre/post）、诙谐谱（monkey_mischief/tang_sutra/market/demon_quip）

【西游记研究共识】
1. 张书绅《西游證道書》（1602）：三教合一论，"释藏以经藏为体，老藏以道德经为体，儒藏以四书为体"
2. 尤侗《東坡戲學》（1705）：认为西游记是"心学"
3. 刘廷玑《在園雜誌》（1687）：认为西游"其意全在佛道"
4. 杨义（1985-）：西游包含儒释道三教合一，"三教归一是作者基本思路"
5. 蔡振前《西游研究方法论》（1989）：文本细读
6. 朱一玄《西游辞典》（1989）：术语/概念工具书

工作方式：
1. 先用工具查询事实，再基于查询结果回答；
2. 涉及多步推理时（如"孙悟空和唐僧的关系链"），可连续调用多个工具；
3. 回答用简体中文，结构清晰，善用小标题与列表；
4. 只陈述工具返回的事实，查不到就明确说明「本体中未收录」，不要脑补；
5. 若工具返回了表格数据，用文字概括要点，不要在正文里手写大表格；
6. 涉及三教论理、诙谐谱等隐性层，可以结合学术研究背景（张书绅/尤侗/杨义等）适度引申，但要明确区分"本体数据"与"研究阐释"。

【重要】：如果本体抽取的数据较少（页数不足 72），要明确告知用户"目前仅抽取了部分页面，统计数字可能偏小"。`;

/* ------------------------- 大模型客户端 ------------------------- */

function chatUrl() {
  const cfg = loadConfig();
  return normalizeBaseUrl(cfg.baseUrl) + '/chat/completions';
}

function authHeaders() {
  const cfg = loadConfig();
  const h = { 'Content-Type': 'application/json' };
  if (cfg.apiKey) h.Authorization = 'Bearer ' + cfg.apiKey;
  if (/openrouter/i.test(cfg.baseUrl || '')) {
    h['HTTP-Referer'] = location.origin || 'https://github.com';
    h['X-Title'] = 'JTW KG Agent';
  }
  return h;
}

async function fetchWithTimeout(url, opts, ms) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: ctl.signal });
  } finally {
    clearTimeout(timer);
  }
}

function sanitizeMsgs(messages) {
  return (messages || [])
    .filter((m) => m && typeof m.role === 'string' && m.role)
    .map((m) => {
      const o = { role: m.role, content: m.content == null ? '' : String(m.content) };
      if (m.role === 'tool') {
        if (m.tool_call_id) o.tool_call_id = m.tool_call_id;
        if (m.name) o.name = m.name;
      } else if (m.tool_calls) {
        o.tool_calls = m.tool_calls;
      }
      return o;
    });
}

async function chatComplete(messages, withTools) {
  const cfg = loadConfig();
  const body = {
    model: cfg.model,
    messages: sanitizeMsgs(messages),
    temperature: typeof cfg.temperature === 'number' ? cfg.temperature : 0.2,
    stream: false,
  };
  if (withTools) {
    body.tools = toolsForLLM();
    body.tool_choice = 'auto';
  }
  let res;
  try {
    res = await fetchWithTimeout(chatUrl(), { method: 'POST', headers: authHeaders(), body: JSON.stringify(body) }, 60000);
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('无法连接模型接口（超时 60s）');
    const mc = mixedContentWarning(loadConfig().baseUrl);
    if (mc) throw new Error(mc);
    throw new Error('无法连接模型接口：' + e.message);
  }
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error('模型接口返回 ' + res.status + '：' + txt.slice(0, 300));
  }
  const data = await res.json();
  const msg = data && data.choices && data.choices[0] && data.choices[0].message;
  if (!msg) throw new Error('模型接口返回格式异常');
  return msg;
}

async function chatStream(messages, onToken) {
  const cfg = loadConfig();
  const body = {
    model: cfg.model,
    messages: sanitizeMsgs(messages),
    temperature: typeof cfg.temperature === 'number' ? cfg.temperature : 0.2,
    stream: true,
  };
  let res;
  try {
    res = await fetchWithTimeout(chatUrl(), { method: 'POST', headers: authHeaders(), body: JSON.stringify(body) }, 180000);
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('模型接口超时 180s');
    const mc = mixedContentWarning(loadConfig().baseUrl);
    if (mc) throw new Error(mc);
    throw new Error('无法连接模型接口：' + e.message);
  }
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error('模型接口返回 ' + res.status + '：' + txt.slice(0, 300));
  }
  if (!res.body) {
    const data = await res.json();
    const txt2 = data.choices?.[0]?.message?.content || '';
    if (onToken) onToken(txt2);
    return txt2;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let full = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith('data:')) continue;
      const payload = t.slice(5).trim();
      if (payload === '[DONE]') continue;
      try {
        const j = JSON.parse(payload);
        const delta = j.choices?.[0]?.delta?.content;
        if (delta) { full += delta; if (onToken) onToken(delta); }
      } catch (_) {}
    }
  }
  return full;
}

/* ------------------------- 状态定义 ------------------------- */

const AgentState = Annotation.Root({
  question: Annotation({ default: () => '' }),
  mode: Annotation({ default: () => 'rule' }),
  msgs: Annotation({ reducer: (a, b) => [...a, ...b], default: () => [] }),
  trace: Annotation({ reducer: (a, b) => [...a, ...b], default: () => [] }),
  blocks: Annotation({ reducer: (a, b) => [...a, ...b], default: () => [] }),
  routeKey: Annotation({ default: () => 'plan' }),
  nextAction: Annotation({ default: () => 'plan' }),
  finalText: Annotation({ default: () => '' }),
  iterations: Annotation({ reducer: (a, b) => a + b, default: () => 0 }),
  error: Annotation({ default: () => '' }),
});

/* ------------------------- 节点实现 ------------------------- */

async function nodePlan(state, config) {
  if (state.mode === 'rule') {
    const r = await route(state.question);
    if (!r) return { nextAction: 'compose', routeKey: 'compose', trace: [{ tool: '规则引擎', label: '未匹配意图' }], finalText: '' };
    return {
      nextAction: 'act',
      routeKey: 'act',
      trace: [{ tool: '规则引擎', label: r.reason || r.tool }],
      msgs: [{ type: 'planned_call', name: r.tool, args: r.args }],
    };
  }
  if (state.iterations >= MAX_TOOL_ROUNDS) return { nextAction: 'compose', routeKey: 'compose' };

  const msg = await chatComplete(state.msgs, true);
  const calls = msg.tool_calls || [];
  const assistantMsg = { role: 'assistant', content: msg.content || '' };
  if (calls.length) assistantMsg.tool_calls = calls;

  if (calls.length) {
    return {
      nextAction: 'act',
      routeKey: 'act',
      msgs: [assistantMsg],
      trace: calls.map((c) => ({ tool: c.function?.name || '工具', label: c.function?.arguments || '' })),
    };
  }
  return { nextAction: 'compose', routeKey: 'compose', msgs: [assistantMsg], finalText: msg.content || '' };
}

async function nodeAct(state) {
  const last = state.msgs[state.msgs.length - 1];
  const blocks = [];
  const newMsgs = [];

  // 规则模式
  if (last && last.type === 'planned_call') {
    const tool = getTool(last.name);
    if (!tool) return { routeKey: 'compose', nextAction: 'compose' };
    const out = await tool.run(last.args || {});
    if (out.blocks && out.blocks.length) blocks.push(...out.blocks);
    return {
      routeKey: 'compose',
      nextAction: 'compose',
      iterations: 1,
      blocks,
      msgs: [{ type: 'tool_result', name: last.name, display: out.text, payload: out.payload }],
      finalText: out.text || '',
    };
  }

  // LLM 模式：顺序执行全部 tool_calls
  const calls = (last && last.tool_calls) || [];
  for (const c of calls) {
    const name = c.function && c.function.name;
    let args = {};
    try { args = JSON.parse((c.function && c.function.arguments) || '{}'); } catch (_) {}
    const tool = getTool(name);
    let out;
    if (!tool) out = { text: '未知工具 ' + name, payload: { error: 'unknown_tool' } };
    else {
      try { out = await tool.run(args); }
      catch (e) { out = { text: '工具 ' + name + ' 执行失败：' + e.message, payload: { error: e.message } }; }
    }
    if (out.blocks && out.blocks.length) blocks.push(...out.blocks);
    newMsgs.push({
      role: 'tool',
      tool_call_id: c.id,
      name,
      content: JSON.stringify(out.payload != null ? out.payload : { text: out.text }).slice(0, 8000),
    });
    newMsgs.push({ type: 'tool_result', name, display: out.text, payload: out.payload });
  }
  return { routeKey: 'plan', nextAction: 'plan', iterations: 1, blocks, msgs: newMsgs };
}

async function nodeCompose(state, config) {
  const onToken = config?.configurable?.onToken;
  const toolResults = state.msgs.filter((m) => m && m.type === 'tool_result');

  if (state.mode === 'rule') {
    if (!toolResults.length) return { finalText: HELP_TEXT };
    const text = toolResults.map((m) => m.display).filter(Boolean).join('\n\n');
    return { finalText: text || HELP_TEXT };
  }

  if (state.finalText && !toolResults.length) return { finalText: state.finalText };

  const msgs = state.msgs.filter((m) => m && m.role);
  if (!msgs.length || msgs[0].role !== 'system') msgs.unshift({ role: 'system', content: SYSTEM_PROMPT });

  let text = '';
  try {
    text = await chatStream(msgs, onToken);
  } catch (e) {
    return { finalText: state.finalText || '生成回答时出错：' + e.message, error: e.message };
  }
  if (!text.trim()) text = '（模型未返回内容）';
  return { finalText: text };
}

/* ------------------------- 构建状态图 ------------------------- */

let GRAPH = null;
function buildGraph() {
  return new StateGraph(AgentState)
    .addNode('plan', nodePlan)
    .addNode('act', nodeAct)
    .addNode('compose', nodeCompose)
    .addEdge(START, 'plan')
    .addConditionalEdges('plan', (s) => s.routeKey, { act: 'act', compose: 'compose' })
    .addConditionalEdges('act', (s) => s.routeKey, { plan: 'plan', compose: 'compose' })
    .addEdge('compose', END)
    .compile();
}
function getGraph() {
  if (!GRAPH) GRAPH = buildGraph();
  return GRAPH;
}

/* ------------------------- 对外接口 ------------------------- */

/**
 * 运行一次问答
 * @param {string} question
 * @param {{onToken?:Function, onStep?:Function}} hooks
 */
export async function runAgent(question, hooks = {}) {
  const cfg = loadConfig();
  const useLLM = hasLLM(cfg);

  const mode = useLLM ? 'llm' : 'rule';
  const msgs = useLLM ? [{ role: 'system', content: SYSTEM_PROMPT }, { role: 'user', content: question }] : [];

  const init = {
    question,
    mode,
    msgs,
    trace: [],
    blocks: [],
    routeKey: 'plan',
    nextAction: 'plan',
    iterations: 0,
    finalText: '',
    error: '',
  };

  let result;
  try {
    result = await getGraph().invoke(init, { configurable: { onToken: hooks.onToken }, recursionLimit: 40 });
  } catch (e) {
    if (useLLM) {
      const fb = await runRoute(question);
      if (fb) {
        return {
          mode: 'rule-fallback',
          text: '> ⚠️ 大模型调用失败（' + e.message + '），已自动降级为本地规则引擎。\n\n' + (fb.result.text || ''),
          blocks: fb.result.blocks || [],
          trace: [{ tool: '规则引擎（降级）', label: fb.route.reason || fb.route.tool }],
          matched: true,
        };
      }
      return { mode: 'error', text: '调用大模型失败：' + e.message, blocks: [], trace: [] };
    }
    return { mode: 'error', text: '执行出错：' + e.message, blocks: [], trace: [] };
  }

  const steps = result.trace || [];
  steps.forEach((s) => { if (hooks.onStep) hooks.onStep(s); });
  const matched = (result.msgs || []).some((m) => m && m.type === 'tool_result');

  return {
    mode: result.mode,
    text: result.finalText || '',
    blocks: result.blocks || [],
    trace: steps,
    matched,
  };
}

export { HELP_TEXT };
