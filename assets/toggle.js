// 繁 / 简 / 白 三态文本切换（全站共用工具条）
//
// 实现要点：
//   - 繁 ↔ 简：opencc-js (assets/vendor/opencc.js) 客户端实时转换，零后端
//   - 白（现代白话）：正文行使用 data 内 text_zh 字段（逐行预译语料），
//     其余界面文字仍走简体转换；译文缺失的行回退显示原文
//   - 逐节点转换：递归遍历 DOM，对每个含中文的 Element 取其原始 textContent、
//     转繁/简后再写回（保留 <span class="src"> 等内嵌结构）
//   - MutationObserver：监听后续动态插入的 DOM（read.html 换回章、compare.html 换底本）
//   - localStorage：jtw.toggle = 't' | 's' | 'w'
//
// 用法（页面）：
//   <script src="assets/vendor/opencc.js"></script>
//   <script src="assets/toggle.js"></script>
// 页面 <body> 内自动挂载浮动工具条，无需额外容器。
//
// 页面 API：
//   window.JTW_TOGGLE = { get(), set(mode), apply(), ready() }

(function () {
  'use strict';

  var STORAGE_KEY = 'jtw.toggle';
  var MODES = {
    t: { label: '繁', desc: '繁体原文' },
    s: { label: '简', desc: '简体' },
    w: { label: '白', desc: '现代白话（已译部分）' },
  };
  var WHITE_MODE = 'w';  // 白话模式：正文行由页面按 text_zh 渲染，此处仅做简体回退

  // 明确不做文本转换的容器
  var SKIP_TAGS = new Set([
    'SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME',
    'TEXTAREA', 'INPUT', 'SELECT', 'OPTION', 'BUTTON',
    'CODE', 'PRE', 'KBD', 'SAMP', 'VAR',
  ]);

  var state = {
    mode: localStorage.getItem(STORAGE_KEY) || 't',
    cn2t: null,
    t2cn: null,
    ready: false,
    observer: null,
    mounted: false,
    converting: false,
  };

  // ---------- OpenCC 初始化 ----------
  var initRetryCount = 0;
  var MAX_INIT_RETRY = 5;
  function initConverters() {
    if (state.ready) return;
    if (typeof window.OpenCC === 'undefined' || !window.OpenCC.Converter) {
      if (initRetryCount < MAX_INIT_RETRY) {
        initRetryCount++;
        setTimeout(initConverters, 100);
      } else {
        console.warn('[JTW toggle] OpenCC 未加载，繁简切换不可用');
      }
      return;
    }
    try {
      // 标准公开 API：Converter({from,to}) 返回裸转换函数 convert(text)
      state.cn2t = window.OpenCC.Converter({ from: 'cn', to: 't' });
      state.t2cn = window.OpenCC.Converter({ from: 't', to: 'cn' });
      state.ready = true;
    } catch (e) {
      console.error('[JTW toggle] OpenCC 初始化失败', e);
      if (initRetryCount < MAX_INIT_RETRY) {
        initRetryCount++;
        setTimeout(initConverters, 100);
      }
    }
  }

  function hasCJK(s) {
    return /[\u4e00-\u9fff\u3400-\u4dbf]/.test(s);
  }

  function convert(text, mode) {
    if (!state.ready || !text || !hasCJK(text)) return text;
    try {
      if (mode === 's' || mode === 'w') return state.t2cn(text);
      if (mode === 't') return state.cn2t(text);
    } catch (e) {
      /* 单点失败不影响整体 */
    }
    return text;
  }

  // ---------- DOM 遍历 ----------
  function shouldSkipEl(el) {
    var p = el;
    while (p && p.parentNode) {
      if (SKIP_TAGS.has(p.tagName)) return true;
      p = p.parentNode;
    }
    // 跳过工具条自身，避免按钮文本被反复转换
    if (el.closest && el.closest('#jtw-toggle')) return true;
    if (el.id === 'jtw-toggle') return true;
    return false;
  }

  // 以"文本节点"为最小转换单元：
  //   原实现只递归 Element children，会跳过 <p>甲<b>乙</b>丙</p> 中"甲""丙"这类
  //   直接挂在混合内容元素下的文本节点，导致繁简切换只转内嵌标签里的文字。
  //   现改为递归 childNodes（含文本节点）；原始文本记录在文本节点自身的
  //   _jtwOrig 属性上（文本节点无法挂 data-* 属性）。
  function walk(el) {
    if (!el || !el.nodeType) return;

    // 文本节点：就地转换
    if (el.nodeType === 3) {
      var txt = el.textContent;
      if (!txt || !hasCJK(txt)) return;
      var parent = el.parentElement;
      if (!parent || shouldSkipEl(parent)) return;
      if (typeof el._jtwOrig === 'undefined') el._jtwOrig = txt;
      var converted = convert(el._jtwOrig, state.mode);
      if (converted !== txt) el.textContent = converted;
      return;
    }

    if (el.nodeType !== 1) return;
    var tag = el.tagName;
    if (tag === 'BR') return;
    if (SKIP_TAGS.has(tag)) return;
    if (shouldSkipEl(el)) return;

    // 递归全部子节点（元素 + 文本），覆盖混合内容
    var child = el.firstChild;
    while (child) {
      walk(child);
      child = child.nextSibling;
    }
  }

  function applyToRoot(root) {
    if (!root) return;
    walk(root);
  }

  function applyAll() {
    if (!state.ready) return;
    // 加防重入锁：避免 MutationObserver 循环触发
    if (state.converting) return;
    state.converting = true;
    try {
      walk(document.body);
    } finally {
      state.converting = false;
    }
  }

  // ---------- 工具条 UI ----------
  var CSS = '' +
    '.jtw-toggle{position:fixed;top:12px;right:16px;z-index:9999;' +
    'display:flex;align-items:center;gap:2px;' +
    'padding:3px;background:rgba(255,253,248,.94);' +
    'border:1px solid rgba(158,43,37,.28);border-radius:16px;' +
    'box-shadow:0 2px 8px rgba(60,40,30,.10);' +
    'font-family:"Songti SC","Noto Serif CJK SC","Noto Serif SC","STSong",serif;}' +
    '.jtw-toggle .tip{font-size:11px;color:#8a7a6a;padding:0 6px 0 8px;letter-spacing:.06em}' +
    '.jtw-toggle button{border:1px solid transparent;background:transparent;' +
    'padding:2px 9px;font-size:13px;line-height:1.4;color:#5a4a3a;' +
    'border-radius:11px;cursor:pointer;letter-spacing:.04em;' +
    'font-family:inherit;transition:all .18s;user-select:none}' +
    '.jtw-toggle button:hover:not([disabled]){background:rgba(232,220,196,.35)}' +
    '.jtw-toggle button.on{color:#9e2b25;background:linear-gradient(180deg,#fdf1ee,#f8e6e2);' +
    'border-color:rgba(158,43,37,.35)}' +
    '.jtw-toggle button[disabled]{opacity:.42;cursor:not-allowed}' +
    '.jtw-toggle .w-tag{font-size:9.5px;color:#a8937a;margin-left:2px;letter-spacing:.02em}' +
    '@media (max-width:640px){.jtw-toggle{top:auto;bottom:10px;right:10px;padding:2px;gap:1px;box-shadow:0 2px 10px rgba(60,40,30,.18)}' +
    '.jtw-toggle .tip{display:none}.jtw-toggle button{padding:2px 8px;font-size:12.5px}}';

  function mountToolbar() {
    if (state.mounted) return;
    state.mounted = true;

    var style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);

    var bar = document.createElement('div');
    bar.className = 'jtw-toggle';
    bar.id = 'jtw-toggle';

    var tip = document.createElement('span');
    tip.className = 'tip';
    tip.textContent = '文本';
    bar.appendChild(tip);

    for (var key of ['t', 's', 'w']) {
      var meta = MODES[key];
      var b = document.createElement('button');
      b.dataset.mode = key;
      b.innerHTML = meta.label + (key === 'w' ? '<span class="w-tag">·</span>' : '');
      if (key === state.mode) b.classList.add('on');
      b.title = meta.desc;
      b.addEventListener('click', function (ev) {
        var target = ev.currentTarget;
        if (target.disabled) return;
        setMode(target.dataset.mode);
      });
      bar.appendChild(b);
    }
    document.body.appendChild(bar);
  }

  function refreshToolbar() {
    var bar = document.getElementById('jtw-toggle');
    if (!bar) return;
    var btns = bar.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      var b = btns[i];
      if (b.dataset.mode === state.mode) b.classList.add('on');
      else b.classList.remove('on');
    }
  }

  // ---------- 主 API ----------
  function setMode(mode) {
    if (mode !== 't' && mode !== 's' && mode !== 'w') return;
    if (mode === state.mode) return;
    state.mode = mode;
    localStorage.setItem(STORAGE_KEY, mode);
    refreshToolbar();
    applyAll();
    // 通知各页面重渲染（如 read.html 按 text_zh 切换正文行）
    try {
      window.dispatchEvent(new CustomEvent('jtw:toggle', { detail: { mode: mode } }));
    } catch (e) { /* 旧浏览器忽略 */ }
  }

  function getMode() { return state.mode; }

  function ready() { return state.ready; }

  window.JTW_TOGGLE = {
    apply: applyAll,
    set: setMode,
    get: getMode,
    ready: ready,
  };

  // ---------- 启动 ----------
  function boot() {
    initConverters();
    mountToolbar();
    // 延迟应用：等待 initConverters 重试完成
    var applyRetry = 0;
    function tryApply() {
      if (state.ready) {
        applyAll();
      } else if (applyRetry < MAX_INIT_RETRY) {
        applyRetry++;
        setTimeout(tryApply, 100);
      }
    }
    tryApply();

    if (window.MutationObserver) {
      var pending = null;
      state.observer = new MutationObserver(function (muts) {
        if (pending) return;
        // 100ms 批量合并：动态渲染密集时减少遍历次数
        pending = setTimeout(function () {
          pending = null;
          if (!state.ready || state.converting) return;
          var changed = [];
          for (var i = 0; i < muts.length; i++) {
            var m = muts[i];
            if (m.type !== 'childList' || !m.addedNodes) continue;
            for (var j = 0; j < m.addedNodes.length; j++) {
              var n = m.addedNodes[j];
              if (n.nodeType === 3) {
                // 新增文本节点：直接就地转换（walk 内部含跳过判断）
                walk(n);
                continue;
              }
              if (n.nodeType !== 1) continue;
              // 跳过工具条自身
              if (n.id === 'jtw-toggle' || (n.querySelector && n.querySelector('#jtw-toggle'))) continue;
              changed.push(n);
            }
          }
          if (!changed.length) return;
          state.converting = true;
          try {
            for (var k = 0; k < changed.length; k++) walk(changed[k]);
          } finally {
            state.converting = false;
          }
        }, 100);
      });
      state.observer.observe(document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
