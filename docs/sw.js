/* sw.js —— 西游记 Agent · Service Worker
 * 目标：让 GitHub Pages 用户第二次打开时秒开，首次也要能离线缓存核心资源。
 * 策略：
 *   - lib/*, data/*, css/*, assets/* 走 Cache First（wasm 引擎、parquet 表全部长期缓存）
 *   - *.js / *.html / data/manifest.json 走 Network First（代码/页面迭代立即生效）
 *   - 其它请求回退到网络
 * 路径说明：GitHub Pages 是 site.github.io/USER/REPO/ 子路径，SCOPE 用 self.registration.scope 自动适配。
 */

const CACHE = 'jtw-kg-v28';
const KEEP = 200; // 缓存条目上限，19 张 parquet + wasm + html/js/css

// SW 注册后 scope 形如 https://host/the-journey-to-the-west/，转成站内根前缀
const SCOPE = self.registration.scope.replace(/[^/]+$/, '');
const toLocal = (u) => u.startsWith(SCOPE) ? u.substring(SCOPE.length - 1) : u;

// JS 代码更新频繁，走 Network First 确保用户拿到最新版
const NETWORK_FIRST = [/\.html$/, /\/data\/manifest\.json$/, /\/data\/pages\//, /\.js$/];
// 数据/样式/库文件稳定，走 Cache First（data/ 下仅 parquet 长期缓存）
const ALWAYS_CACHE = [/\/lib\//, /\/data\/[^/]*\.parquet/, /\/css\//, /\/assets\//];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  // install 阶段预缓存 index.html（scope 相对，兼容 GitHub Pages 子路径）
  const idxUrl = SCOPE + 'index.html';
  e.waitUntil(
    fetch(idxUrl).then((resp) => {
      if (resp.ok) return caches.open(CACHE).then((c) => c.put(idxUrl, resp));
    }).catch(() => {})
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  const local = toLocal(req.url);
  const isNetworkFirst = NETWORK_FIRST.some((r) => r.test(local));
  const isCacheFirst = ALWAYS_CACHE.some((r) => r.test(local));

  // 网络优先：HTML 入口和清单（页面/代码更新后立即生效）
  if (isNetworkFirst) {
    e.respondWith(
      fetch(req)
        .then((resp) => {
          if (resp.ok && resp.type === 'basic') {
            // HTML 缓存前校验：必须含 <nav>，否则视为 404/错误页不缓存
            if (/\.html$/.test(local)) {
              resp.clone().text().then((text) => {
                if (text.includes('<nav>')) {
                  caches.open(CACHE).then((c) => c.put(req, resp.clone())).catch(() => {});
                }
              });
            } else {
              const clone = resp.clone();
              caches.open(CACHE).then((c) => c.put(req, clone)).catch(() => {});
            }
          }
          return resp;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // 缓存优先：库/数据/样式/图片（wasm 引擎、parquet 表长期复用）
  if (isCacheFirst) {
    e.respondWith(
      caches.match(req).then((hit) => {
        if (hit) return hit;
        return fetch(req).then((resp) => {
          if (resp.ok && resp.type === 'basic') {
            const clone = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, clone)).catch(() => {});
          }
          return resp;
        });
      })
    );
    return;
  }

  // 兜底：直接走网络
  e.respondWith(fetch(req));
});

// 版本升级时按容量裁掉最旧缓存
self.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'TRIM') {
    caches.open(CACHE).then((c) => {
      return c.keys().then((reqs) => {
        if (reqs.length <= KEEP) return;
        return Promise.all(reqs.slice(0, reqs.length - KEEP).map((r) => c.delete(r)));
      });
    });
  }
});
