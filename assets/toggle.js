// 繁 / 简 / 白 三态文本切换（全站共用工具条）
//
// 实现要点：
//   - 繁 ↔ 简：opencc-js (assets/vendor/opencc.js) 客户端实时转换，零后端
//   - 白（民国白话·胡适式）：UI 预留开关，暂无语料，置灰禁用
//   - 逐节点转换：递归遍历 DOM，对每个含中文的 Element 取其原始 textContent、
//     转繁/简后再写回（保留 <span class="src"> 等内嵌结构）
//   - MutationObserver：监听后续动态插入的 DOM（read.html 换回章、compare.html 换底本）
//   - localStorage：jtw.toggle = 't' | 's'
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
    w: { label: '白', desc: '民国白话（胡适式）— 语料库准备中' },
  };
  var WHITE_MODE = 'w';  // 仅 UI 占位，无实际转换

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
      // 直接使用 ConverterFactory + Locale，避免 Converter 的参数检查在某些环境下异常
      state.cn2t = window.OpenCC.ConverterFactory(window.OpenCC.Locale.from.cn);
      state.t2cn = window.OpenCC.ConverterFactory(window.OpenCC.Locale.to.cn);
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
      if (mode === 's') return state.t2cn.convert(text);
      if (mode === 't') return state.cn2t.convert(text);
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

  function walk(el) {
    if (!el || !el.nodeType) return;

    // 文本节点：找到祖先 Element，由其负责转换（避免直接改叶子后重复计算）
    if (el.nodeType === 3) return;
    if (el.nodeType !== 1) return;

    var tag = el.tagName;
    if (tag === 'BR') return;
    if (SKIP_TAGS.has(tag)) return;
    if (shouldSkipEl(el)) return;

    // 若含 Element 子节点：不转换自身 textContent（否则会抹掉子元素），递归子节点
    if (el.children && el.children.length > 0) {
      for (var i = 0; i < el.children.length; i++) walk(el.children[i]);
      return;
    }

    // 叶元素：只含文本节点
    var orig = el.getAttribute('data-jtw-orig');
    if (orig === null) {
      orig = el.textContent;
      if (orig && hasCJK(orig)) {
        el.setAttribute('data-jtw-orig', orig);
      } else {
        // 纯 ASCII/空白，直接跳过（不再设置属性，避免缓存污染）
        return;
      }
    }
    var converted = convert(orig, state.mode);
    if (converted !== el.textContent) el.textContent = converted;
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
    '.jtw-toggle .w-tag{font-size:9.5px;color:#a8937a;margin-left:2px;letter-spacing:.02em}';

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
      if (key === WHITE_MODE) {
        b.disabled = true;
        b.title = meta.desc;
      } else {
        b.title = meta.desc;
      }
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
    if (mode !== 't' && mode !== 's') return;
    if (mode === state.mode) return;
    state.mode = mode;
    localStorage.setItem(STORAGE_KEY, mode);
    refreshToolbar();
    applyAll();
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
