/* ============================================================
   main.js —— 西游记 Agent · 前端入口
   启动 DuckDB-WASM → 装载 19 张本体论表 → 渲染聊天界面 → 绑定 UI 事件
   ============================================================ */

import { initDB, isReady, getTableInfo, overview } from './db.js';
import { runAgent } from './agent.js';
import { loadConfig, saveConfig, clearConfig, hasLLM, PROVIDER_PRESETS, normalizeBaseUrl } from './config.js';

const $ = (id) => document.getElementById(id);

const state = {
  busy: false,
  chatHistory: [],
};

/* ================= 启动 ================= */

async function boot() {
  initUI();
  bindEvents();
  const overlay = $('loadingOverlay');
  const text = $('loadingText');
  try {
    await initDB((msg) => {
      text.textContent = msg;
    });
    overlay.classList.add('hidden');
    setStatus('ok', '就绪');
    updateWelcomeStats();
    // 尝试自动注册 Service Worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  } catch (e) {
    overlay.classList.add('hidden');
    setStatus('err', '初始化失败');
    text.textContent = '初始化失败：' + e.message;
    console.error(e);
  }
}

/* ================= UI 初始化 ================= */

function initUI() {
  // 模型预设下拉
  const presetSel = $('providerPreset');
  if (presetSel) {
    const items = PROVIDER_PRESETS.map((p) => `<option value="${p.id}">${p.label}</option>`).join('');
    presetSel.innerHTML = items;
  }
  const cfg = loadConfig();
  $('baseUrl').value = cfg.baseUrl || '';
  $('apiKey').value = cfg.apiKey || '';
  $('modelName').value = cfg.model || '';
  updateModeBadge();
}

function bindEvents() {
  // 新对话
  $('newChatBtn').addEventListener('click', () => {
    state.chatHistory = [];
    $('chatMessages').innerHTML = '';
    $('chatHero').classList.remove('hidden');
  });

  // 侧栏知识入口（nav-link data-q）
  document.querySelectorAll('.nav-link[data-q]').forEach((a) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const q = a.getAttribute('data-q');
      if (!q) return;
      $('userInput').value = q;
      sendQuestion();
    });
  });

  // 发送
  $('sendBtn').addEventListener('click', sendQuestion);
  $('userInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuestion();
    }
  });

  // 模型预设切换
  $('providerPreset').addEventListener('change', (e) => {
    const preset = PROVIDER_PRESETS.find((p) => p.id === e.target.value);
    if (!preset) return;
    $('baseUrl').value = preset.baseUrl;
    $('modelName').value = preset.model;
  });

  // 保存设置
  $('saveSettings').addEventListener('click', () => {
    saveConfig({
      baseUrl: $('baseUrl').value.trim(),
      apiKey: $('apiKey').value.trim(),
      model: $('modelName').value.trim(),
    });
    updateModeBadge();
    alert('设置已保存（仅本地）');
  });
  $('clearSettings').addEventListener('click', () => {
    if (!confirm('清除本地配置？')) return;
    clearConfig();
    $('baseUrl').value = '';
    $('apiKey').value = '';
    $('modelName').value = '';
    updateModeBadge();
  });

  // 测试连接
  $('testConnection').addEventListener('click', async () => {
    const cfg = { baseUrl: $('baseUrl').value.trim(), apiKey: $('apiKey').value.trim(), model: $('modelName').value.trim() };
    if (!cfg.baseUrl || !cfg.apiKey) {
      $('testResult').innerHTML = '<span style="color:#c33">请先填写 baseUrl 与 apiKey</span>';
      return;
    }
    $('testResult').innerHTML = '测试中…';
    try {
      const res = await fetch(normalizeBaseUrl(cfg.baseUrl) + '/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + cfg.apiKey },
        body: JSON.stringify({ model: cfg.model, messages: [{ role: 'user', content: 'ping' }], max_tokens: 5 }),
      });
      if (res.ok) $('testResult').innerHTML = '<span style="color:#0a0">✓ 连接成功</span>';
      else $('testResult').innerHTML = `<span style="color:#c33">✗ HTTP ${res.status}</span>`;
    } catch (e) {
      $('testResult').innerHTML = '<span style="color:#c33">✗ ' + e.message + '</span>';
    }
  });

  // 快速提问按钮
  const quick = [
    { text: '图谱总览', q: '知识图谱总览' },
    { text: '孙悟空', q: '孙悟空人物画像' },
    { text: '唐僧 × 悟空', q: '唐僧和孙悟空的关系' },
    { text: '三教论理', q: '三教论理分析' },
    { text: '诙谐谱', q: '诙谐点查找' },
    { text: '法宝', q: '法宝查询' },
  ];
  const wrap = $('quickActions');
  if (wrap) {
    wrap.innerHTML = quick.map((x) => `<button class="quick-btn" data-q="${x.q}">${x.text}</button>`).join('');
    wrap.querySelectorAll('.quick-btn').forEach((b) => {
      b.addEventListener('click', () => {
        $('userInput').value = b.dataset.q;
        sendQuestion();
      });
    });
  }
}

function updateModeBadge() {
  const has = hasLLM();
  const badge = $('modeBadge');
  if (!badge) return;
  badge.textContent = has ? '🤖 大模型' : '📏 规则引擎';
  badge.style.background = has ? '#4a63e7' : '#6c5b3d';
}

function setStatus(kind, text) {
  const dot = $('dbStatus').querySelector('.status-dot');
  const txt = $('dbStatus').querySelector('.status-text');
  dot.className = 'status-dot ' + (kind === 'ok' ? 'ok' : kind === 'err' ? 'err' : 'loading');
  txt.textContent = text;
}

async function updateWelcomeStats() {
  if (!isReady()) return;
  try {
    const o = await overview();
    const wrap = $('welcomeStats');
    if (!wrap) return;
    wrap.classList.remove('hidden');
    wrap.innerHTML = [
      ['版本', o.editions],
      ['页', o.pages],
      ['行', o.lines],
      ['实体', o.entities],
      ['关系', o.relationships],
      ['事件', o.events],
      ['章节', o.chapters],
      ['评点', o.annotations],
    ].map(([k, v]) => `<div class="stat-item"><span class="stat-num">${v}</span><span class="stat-label">${k}</span></div>`).join('');
  } catch (e) { console.warn('overview failed', e); }
}

/* ================= 发送与渲染 ================= */

async function sendQuestion() {
  if (state.busy) return;
  const input = $('userInput');
  const q = (input.value || '').trim();
  if (!q) return;
  input.value = '';

  $('chatHero').classList.add('hidden');
  appendMessage('user', q);

  state.busy = true;
  $('sendBtn').disabled = true;
  $('sendBtn').textContent = '…';

  const userMsg = state.chatHistory[state.chatHistory.length - 1];
  const replyEl = appendMessage('assistant', '', { streaming: true });

  const started = Date.now();
  const stepEl = replyEl.querySelector('.streaming-text');

  try {
    const result = await runAgent(q, {
      onToken: (token) => {
        if (stepEl) stepEl.textContent += token;
        autoScroll();
      },
      onStep: (s) => {
        // 追踪步骤（可选）
      },
    });
    const dur = ((Date.now() - started) / 1000).toFixed(1);
    const meta = `> 模式：${result.mode || 'rule'}｜工具：${(result.trace || []).map((t) => t.tool).join(' → ') || '—'}｜耗时 ${dur}s\n\n`;
    if (stepEl) stepEl.textContent = '';
    replyEl.querySelector('.msg-body').innerHTML = '';
    appendRich(replyEl, meta + result.text || '（空响应）', result.blocks || []);
  } catch (e) {
    if (stepEl) stepEl.textContent += '\n\n⚠️ ' + e.message;
    console.error(e);
  } finally {
    state.busy = false;
    $('sendBtn').disabled = false;
    $('sendBtn').textContent = '➤';
    autoScroll();
  }
}

function appendMessage(role, text, opts = {}) {
  const wrap = $('chatMessages');
  const div = document.createElement('div');
  div.className = 'msg ' + role;

  const head = document.createElement('div');
  head.className = 'msg-head';
  head.innerHTML = `<span class="msg-role">${role === 'user' ? '你' : 'Agent'}</span>`;
  if (opts.streaming) head.innerHTML += '<span class="msg-loading">思考中…</span>';

  const body = document.createElement('div');
  body.className = 'msg-body';

  if (opts.streaming) {
    const stream = document.createElement('div');
    stream.className = 'streaming-text';
    stream.textContent = text;
    body.appendChild(stream);
  } else {
    body.innerHTML = renderText(text);
  }

  div.appendChild(head);
  div.appendChild(body);
  wrap.appendChild(div);

  state.chatHistory.push({ role, text });
  autoScroll();
  return div;
}

function appendRich(msgEl, text, blocks) {
  const body = msgEl.querySelector('.msg-body');
  body.innerHTML = '';
  const main = document.createElement('div');
  main.className = 'md-content';
  main.innerHTML = renderText(text);
  body.appendChild(main);
  if (blocks && blocks.length) {
    for (const b of blocks) body.appendChild(renderBlock(b));
  }
}

function renderBlock(b) {
  if (!b) return document.createElement('div');
  const wrap = document.createElement('div');
  wrap.className = 'block ' + (b.type || 'table');
  if (b.title) {
    const t = document.createElement('div');
    t.className = 'block-title';
    t.textContent = b.title;
    wrap.appendChild(t);
  }
  if (b.type === 'table' && Array.isArray(b.rows)) {
    const table = document.createElement('table');
    table.className = 'data-table';
    if (b.columns) {
      const thead = document.createElement('thead');
      thead.innerHTML = '<tr>' + b.columns.map((c) => `<th>${escapeHtml(String(c))}</th>`).join('') + '</tr>';
      table.appendChild(thead);
    }
    const tbody = document.createElement('tbody');
    for (const row of b.rows) {
      const tr = document.createElement('tr');
      for (const cell of row) tr.innerHTML += `<td>${escapeHtml(cell == null ? '' : String(cell))}</td>`;
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    wrap.appendChild(table);
  } else if (b.type === 'bar' && Array.isArray(b.data)) {
    const max = Math.max(...b.data.map((d) => d.value || 0), 1);
    const ul = document.createElement('ul');
    ul.className = 'bar-list';
    for (const d of b.data) {
      const li = document.createElement('li');
      const pct = Math.round(((d.value || 0) / max) * 100);
      li.innerHTML = `<div class="bar-row"><span class="bar-label">${escapeHtml(d.label)}</span><div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div><span class="bar-num">${d.value}</span></div>`;
      ul.appendChild(li);
    }
    wrap.appendChild(ul);
  }
  return wrap;
}

function renderText(text) {
  return renderMarkdownLite(text);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/** 简易 markdown-lite 渲染（支持标题/列表/代码/加粗/引用/换行） */
function renderMarkdownLite(md) {
  if (!md) return '';
  const lines = String(md).split('\n');
  const out = [];
  let inList = false;
  let inCode = false;
  let codeBuf = '';
  for (const line of lines) {
    if (line.trim().startsWith('```')) {
      if (!inCode) { inCode = true; codeBuf = ''; inList = false; }
      else { out.push('<pre class="code"><code>' + escapeHtml(codeBuf) + '</code></pre>'); inCode = false; }
      continue;
    }
    if (inCode) { codeBuf += line + '\n'; continue; }
    const mH = line.match(/^(#{1,4})\s+(.*)$/);
    if (mH) {
      if (inList) { out.push('</ul>'); inList = false; }
      const lvl = mH[1].length;
      out.push(`<h${lvl} class="md-h${lvl}">${inline(mH[2])}</h${lvl}>`);
      continue;
    }
    const mQ = line.match(/^>\s?(.*)$/);
    if (mQ) {
      if (inList) { out.push('</ul>'); inList = false; }
      out.push(`<blockquote>${inline(mQ[1])}</blockquote>`);
      continue;
    }
    const mL = line.match(/^\s*[-*]\s+(.*)$/);
    if (mL) {
      if (!inList) { out.push('<ul class="md-list">'); inList = true; }
      out.push(`<li>${inline(mL[1])}</li>`);
      continue;
    }
    if (!line.trim()) { if (inList) { out.push('</ul>'); inList = false; } continue; }
    if (inList) { out.push('</ul>'); inList = false; }
    out.push(`<p>${inline(line)}</p>`);
  }
  if (inList) out.push('</ul>');
  if (inCode) out.push('<pre class="code"><code>' + escapeHtml(codeBuf) + '</code></pre>');
  return out.join('');
}

function inline(s) {
  return escapeHtml(s)
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
}

function autoScroll() {
  const sc = $('chatScroll');
  sc.scrollTop = sc.scrollHeight;
}

/* ================= 启动 ================= */
boot();
