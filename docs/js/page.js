/* ============================================================
   page.js —— 只读页面的数据加载 helper（不加载 DuckDB-WASM）
   只依赖 data/pages/{page}.json（构建期由 export_pages.py 生成）。
   Agent 页仍用 db.js（需要实时查询）。
   ============================================================ */

/* Service Worker 注册：所有页面共享一份缓存策略（幂等） */
if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
  try {
    navigator.serviceWorker.register('./sw.js', { scope: './' }).catch(() => {});
  } catch (_) {}
}

function assetUrl(relPath) {
  const baseURI = document.baseURI;
  const lastSlash = baseURI.lastIndexOf('/');
  const base = lastSlash === -1 ? '/' : baseURI.substring(0, lastSlash + 1);
  return new URL(relPath, base).href;
}

const _cache = new Map();

/**
 * 加载某个页面的静态 JSON 数据
 * @param {string} page 页面名（如 'read' / 'entities' / 'graph'）
 * @returns {Promise<Object>} 形如 { chapters: [...], lines: [...] } 的字典
 */
export async function loadPageData(page) {
  if (_cache.has(page)) return _cache.get(page);
  const url = assetUrl(`data/pages/${page}.json?v=099`);
  const resp = await fetch(url, { cache: 'no-cache' });
  if (!resp.ok) throw new Error(`页面数据加载失败（HTTP ${resp.status} @ ${url}）`);
  const data = await resp.json();
  _cache.set(page, data);
  return data;
}
