/* ============================================================
   db.js —— 西游记知识图谱 · DuckDB-WASM 数据层（简化版）
   在浏览器本地加载本体论 Parquet 数据并执行 SQL。
   ============================================================ */

import * as duckdb from '../lib/duckdb/duckdb.bundle.js';

let DB = null;
let CONN = null;
let READY = false;
let INITED = false;

function assetUrl(relPath) {
  return new URL('../' + relPath, import.meta.url).href;
}

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
 * 初始化数据库
 * @param {(msg:string)=>void} onProgress
 */
export async function initDB(onProgress) {
  if (INITED) { if (!READY) return; return; }
  INITED = true;
  const log = (m) => { try { onProgress && onProgress(m); } catch (_) {} };

  log('正在读取数据清单…');
  const resp = await fetch(assetUrl('data/manifest.json'), { cache: 'no-cache' });
  if (!resp.ok) throw new Error(`数据清单加载失败（HTTP ${resp.status}）`);
  const manifest = await resp.json();
  const names = (manifest.tables || []).map(t => t.name);
  if (!names.length) throw new Error('数据清单为空');

  log('正在初始化 DuckDB WASM 引擎…');
  const mvpWasm = assetUrl('lib/duckdb/duckdb-mvp.wasm');
  const mvpWorker = assetUrl('lib/duckdb/duckdb-browser-mvp.worker.js');
  const ehWasm = assetUrl('lib/duckdb/duckdb-eh.wasm');
  const ehWorker = assetUrl('lib/duckdb/duckdb-browser-eh.worker.js');
  const localBundles = {
    mvp: { mainModule: mvpWasm, mainWorker: mvpWorker },
    eh: { mainModule: ehWasm, mainWorker: ehWorker },
   _roi: { mainModule: ehWasm, mainWorker: ehWorker },
  };
  let bundle = await duckdb.selectBundle(localBundles);
  if (!bundle || !bundle.mainModule) bundle = localBundles.eh;

  // Brotli 解压（可选）
  const wasmUrl = bundle.mainModule;
  const wasmBrUrl = wasmUrl + '.br';
  let effectiveWasmUrl = wasmUrl;
  if (typeof DecompressionStream !== 'undefined') {
    try {
      log('正在下载并解压 WASM 引擎…');
      const brResp = await fetch(wasmBrUrl, { cache: 'force-cache' });
      if (brResp.ok) {
        const brBuf = await brResp.arrayBuffer();
        const blob = new Blob([brBuf]);
        const dsStream = blob.stream().pipeThrough(new DecompressionStream('br'));
        const wasmBuf = await new Response(dsStream).arrayBuffer();
        effectiveWasmUrl = URL.createObjectURL(new Blob([wasmBuf], { type: 'application/wasm' }));
        bundle = Object.assign({}, bundle, { mainModule: effectiveWasmUrl });
      }
    } catch (_) {}
  }

  const workerScript = `importScripts("${bundle.mainWorker}");`;
  let worker;
  try {
    const workerBlobUrl = URL.createObjectURL(new Blob([workerScript], { type: 'text/javascript' }));
    worker = new Worker(workerBlobUrl);
  } catch (e) {
    worker = new Worker(bundle.mainWorker);
  }

  let logger = null;
  try { logger = new duckdb.ConsoleLogger(); } catch (_) { logger = null; }

  DB = new duckdb.AsyncDuckDB(logger, worker);
  await DB.instantiate(bundle.mainModule, bundle.prelude);
  if (effectiveWasmUrl.startsWith('blob:')) URL.revokeObjectURL(effectiveWasmUrl);

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
