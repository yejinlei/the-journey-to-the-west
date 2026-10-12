/* sw.js —— 西游记 Agent · Service Worker
 * 目标：让 GitHub Pages 用户第二次打开时秒开，首次也要能离线缓存核心资源。
 * 策略：
 *   - lib/*, data/*, css/*, js/*（不含 main.js）走 Cache First
 *   - index.html, data/manifest.json 走 Network First（数据/代码迭代时能立即生效）
 *   - 其它请求回退到网络
 */

const CACHE = 'jtw-kg-v1';
const KEEP = 60; // 缓存条目上限，DuckDB-WASM + 19 张表约 40MB

const ALWAYS_CACHE = [/^\/lib\//, /^\/data\//, /^\/css\//, /^\/js\//];
const NETWORK_FIRST = [/^\/index\.html$/, /^\/data\/manifest\.json$/];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(['/index.html']).catch(() => {})));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // 网络优先：HTML 入口和清单
  if (NETWORK_FIRST.some((r) => r.test(url.pathname))) {
    e.respondWith(
      fetch(req)
        .then((resp) => {
          const clone = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, clone)).catch(() => {});
          return resp;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // 缓存优先：库/数据/样式
  if (ALWAYS_CACHE.some((r) => r.test(url.pathname))) {
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
