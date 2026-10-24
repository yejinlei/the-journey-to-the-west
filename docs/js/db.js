/* ============================================================
   db.js —— 西游记知识图谱 · DuckDB-WASM 数据层（简化版）
   在浏览器本地加载本体论 Parquet 数据并执行 SQL。
   跨页复用：wasm 解压后写 IndexedDB（`jtw-wasm/v1`），下次切页直接取用。
   ============================================================ */

import * as duckdb from '../lib/duckdb/duckdb.bundle.js';

/* Service Worker 注册：所有页面共享一份缓存策略 */
if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
  try {
    navigator.serviceWorker.register('./sw.js', { scope: './' }).catch(() => {});
  } catch (_) {}
}

let DB = null;
let CONN = null;
let READY = false;
let INITED = false;
let INIT_PROMISE = null; // 防止并发切页触发两次 init

function assetUrl(relPath) {
  const baseURI = document.baseURI;
  const lastSlash = baseURI.lastIndexOf('/');
  const base = lastSlash === -1 ? '/' : baseURI.substring(0, lastSlash + 1);
  return new URL(relPath, base).href;
}

function bust(url) { return url + (url.includes('?') ? '&' : '?') + 'v=' + Date.now(); }

function normalizeValue(v) {
  if (v === null || v === undefined) return null;
  if (typeof v === 'bigint') return Number(v);
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  if (typeof v === 'object') {
    if (v.constructor && v.constructor.name === 'Decimal') return Number(v.toString());
    try { return JSON.stringify(v); } catch (_) { return String(v); }
  }
  return v;
}

/* ---------------- IndexedDB：缓存解压后的 wasm ---------------- */

const IDB_NAME = 'jtw-cache';
const IDB_VER = 1;
const IDB_STORE = 'files';
const WASM_KEY = 'duckdb-eh.wasm';

function openIDB() {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') return reject(new Error('no IDB'));
    const req = indexedDB.open(IDB_NAME, IDB_VER);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(IDB_STORE)) db.createObjectStore(IDB_STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idbGet(key) {
  try {
    const db = await openIDB();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(IDB_STORE, 'readonly');
      const r = tx.objectStore(IDB_STORE).get(key);
      r.onsuccess = () => resolve(r.result);
      r.onerror = () => reject(r.error);
    });
  } catch (_) { return null; }
}

async function idbPut(key, buf) {
  try {
    const db = await openIDB();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(IDB_STORE, 'readwrite');
      tx.objectStore(IDB_STORE).put(buf, key);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
  } catch (_) {}
}

/* ---------------- 对外接口 ---------------- */

export function isReady() { return READY; }

export async function query(sql) {
  if (!READY) throw new Error('数据库尚未就绪');
  const result = await CONN.query(sql);
  const columns = result.schema.fields.map((f) => f.name);
  const rows = result.toArray().map((row) => {
    const o = {};
    for (const f of result.schema.fields) o[f.name] = normalizeValue(row[f.name]);
    return o;
  });
  return { columns, rows };
}

export async function scalar(sql) {
  const r = await query(sql);
  if (!r.rows.length) return null;
  const first = r.rows[0];
  const k = Object.keys(first)[0];
  return first[k];
}

/**
 * 初始化数据库（幂等 + 并发安全）
 * @param {(msg:string)=>void} onProgress
 */
export function initDB(onProgress) {
  if (INIT_PROMISE) return INIT_PROMISE;
  if (INITED) {
    if (READY) return Promise.resolve();
    // 上一次启动进行中，返回同一个 promise
    return INIT_PROMISE || Promise.resolve();
  }
  INITED = true;
  INIT_PROMISE = _initDB(onProgress);
  INIT_PROMISE.catch(() => { INITED = false; INIT_PROMISE = null; });
  return INIT_PROMISE;
}

async function _initDB(onProgress) {
  const log = (m) => { try { onProgress && onProgress(m); } catch (_) {} };

  log('正在读取数据清单…');
  const manUrl = bust(assetUrl('data/manifest.json'));
  const resp = await fetch(manUrl, { cache: 'no-store' });
  if (!resp.ok) throw new Error(`数据清单加载失败（HTTP ${resp.status} @ ${manUrl}）`);
  const manifest = await resp.json();
  const names = (manifest.tables || []).map(t => t.name);
  if (!names.length) throw new Error('数据清单为空');

  log('正在初始化 DuckDB WASM 引擎…');
  // 强制使用 EH（异常处理版），避免 selectBundle 同时触发 MVP + EH 两套 wasm 下载
  const ehWasm = assetUrl('lib/duckdb/duckdb-eh.wasm');
  const ehWorker = assetUrl('lib/duckdb/duckdb-browser-eh.worker.js');
  const bundle = { mainModule: ehWasm, mainWorker: ehWorker };

  // 解压后的 wasm 走 IndexedDB 缓存：首次下载，之后切页复用
  const wasmBytes = await getOrFetchWasm(ehWasm, log);

  const workerScript = `importScripts("${ehWorker}");`;
  const workerBlobUrl = URL.createObjectURL(new Blob([workerScript], { type: 'text/javascript' }));
  const worker = new Worker(workerBlobUrl);

  let logger = null;
  try { logger = new duckdb.ConsoleLogger(); } catch (_) { logger = null; }

  DB = new duckdb.AsyncDuckDB(logger, worker);
  // 传 ArrayBuffer 而非 URL，让 duckdb 直接用内存字节，避免二次 fetch .wasm
  if (typeof DB.instantiateWithBuffer === 'function') {
    await DB.instantiateWithBuffer(wasmBytes, bundle.prelude);
  } else if (typeof DB.instantiateWithModule === 'function') {
    const mod = await WebAssembly.Module(wasmBytes);
    await DB.instantiateWithModule(mod, bundle.prelude);
  } else {
    const wasmBlob = new Blob([wasmBytes], { type: 'application/wasm' });
    const effectiveUrl = URL.createObjectURL(wasmBlob);
    try { await DB.instantiate(effectiveUrl, bundle.prelude); }
    finally { URL.revokeObjectURL(effectiveUrl); }
  }

  log('正在装载本体论数据表…');
  CONN = await DB.connect();

  const hasBuffer = typeof DB.registerFileBuffer === 'function';
  const hasFileURL = typeof DB.registerFileURL === 'function';

  let loaded = 0;
  for (const name of names) {
    const url = assetUrl(`data/${name}.parquet`);
    const resp2 = await fetch(url, { cache: 'force-cache' });
    if (!resp2.ok) continue;
    const buf = await resp2.arrayBuffer();
    const key = `mem:///${name}.parquet`;
    let tableReady = false;

    if (!tableReady && hasBuffer) {
      try {
        await DB.registerFileBuffer(key, new Uint8Array(buf));
        await CONN.query(`CREATE OR REPLACE TABLE "${name}" AS SELECT * FROM read_parquet('${key}')`);
        tableReady = true;
      } catch (e) { console.warn(`[db] registerFileBuffer ${key} 失败: ${e.message}`); }
    }
    if (!tableReady && hasFileURL) {
      try {
        const rn = await DB.registerFileURL(url, key);
        await CONN.query(`CREATE OR REPLACE TABLE "${name}" AS SELECT * FROM read_parquet('${rn || key}')`);
        tableReady = true;
      } catch (e) { console.warn(`[db] registerFileURL ${key} 失败: ${e.message}`); }
    }
    if (!tableReady) {
      try {
        await CONN.query(`CREATE OR REPLACE TABLE "${name}" AS SELECT * FROM read_parquet('${url.replace(/'/g, "''")}')`);
        tableReady = true;
      } catch (e) { console.warn(`[db] direct URL read ${key} 失败: ${e.message}`); }
    }
    if (tableReady) loaded++;
    else console.warn(`[db] ✗ ${name} 加载失败`);
  }
  console.info(`[db] 已加载 ${loaded}/${names.length} 张表`);
  READY = true;
  log('数据库就绪');
}

/**
 * 获取（解压后的）wasm 字节：
 *   1. IndexedDB 命中 → 直接返回
 *   2. 未命中 → 下载 .br → Brotli 解压 → 写 IndexedDB → 返回
 *   3. Brotli 失败 → fallback 到 fetch 原始 .wasm
 */
async function getOrFetchWasm(wasmUrl, log) {
  const cached = await idbGet(WASM_KEY);
  if (cached && cached.byteLength) {
    log('命中本地 WASM 缓存…');
    return cached;
  }

  log('正在下载并解压 WASM 引擎（首次，约 5MB）…');
  const brUrl = wasmUrl + '.br';

  if (typeof DecompressionStream !== 'undefined') {
    try {
      const brResp = await fetch(brUrl, { cache: 'force-cache' });
      if (brResp.ok) {
        const brBuf = await brResp.arrayBuffer();
        const blob = new Blob([brBuf]);
        const dsStream = blob.stream().pipeThrough(new DecompressionStream('br'));
        const wasmResp = await new Response(dsStream);
        const wasmBuf = await wasmResp.arrayBuffer();
        // 后台异步写入 IndexedDB，不阻塞初始化
        idbPut(WASM_KEY, wasmBuf).catch(() => {});
        return wasmBuf;
      }
    } catch (e) {
      console.warn('[db] Brotli 解压失败，fallback 到原始 wasm:', e);
    }
  }

  log('正在下载 WASM 引擎（原始，约 35MB）…');
  const rawResp = await fetch(wasmUrl, { cache: 'force-cache' });
  if (!rawResp.ok) throw new Error(`WASM 下载失败（HTTP ${rawResp.status}）`);
  const rawBuf = await rawResp.arrayBuffer();
  idbPut(WASM_KEY, rawBuf).catch(() => {});
  return rawBuf;
}
