/* ============================================================
   db.js —— 西游记知识图谱 · DuckDB-WASM 数据层
   在浏览器本地加载本体论 Parquet 数据并执行 SQL。
   兼容 GitHub Pages 子路径部署（用 import.meta.url 解析资源路径）。
   ============================================================ */

import * as duckdb from '../lib/duckdb/duckdb.bundle.js';

let DB = null;
let CONN = null;
let READY = false;
let TABLE_INFO = [];

export function isReady() { return READY; }
export function getTableInfo() { return TABLE_INFO; }

function assetUrl(relPath) {
  return new URL('../' + relPath, import.meta.url).href;
}

/** 读取数据清单（结构：{tables:[{name,path,rows,size_bytes}], counts:{}, ...}） */
async function fetchManifest() {
  const res = await fetch(assetUrl('data/manifest.json'), { cache: 'no-cache' });
  if (!res.ok) throw new Error(`数据清单加载失败（HTTP ${res.status}）`);
  const m = await res.json();
  // 转换为 name -> meta 映射，db.js 内部以这个格式消费
  const map = {};
  for (const t of (m.tables || [])) {
    map[t.name] = { source: t.path, rows: t.rows };
  }
  return map;
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

/** 尝试建表：读已注册的 key，返回是否成功 */
async function tryCreateTable(name, key) {
  try {
    await CONN.query(`CREATE OR REPLACE TABLE "${name}" AS SELECT * FROM read_parquet('${key}')`);
    return true;
  } catch (e) {
    console.warn(`[db] CREATE TABLE "${name}" 失败: ${e.message}`);
    return false;
  }
}

/**
 * 初始化数据库
 * @param {(msg:string)=>void} onProgress
 */
export async function initDB(onProgress) {
  if (READY) return;
  const log = (m) => { try { onProgress && onProgress(m); } catch (_) {} };

  log('正在读取数据清单…');
  const manifest = await fetchManifest();
  const names = Object.keys(manifest);
  if (!names.length) throw new Error('数据清单为空，请确认 04_knowledge_data/manifest.json 已生成');

  log('正在初始化 DuckDB WASM 引擎…');
  const mvpWasm = assetUrl('lib/duckdb/duckdb-mvp.wasm');
  const mvpWorker = assetUrl('lib/duckdb/duckdb-browser-mvp.worker.js');
  const ehWasm = assetUrl('lib/duckdb/duckdb-eh.wasm');
  const ehWorker = assetUrl('lib/duckdb/duckdb-browser-eh.worker.js');
  const localBundles = {
    mvp: { mainModule: mvpWasm, mainWorker: mvpWorker },
    eh: { mainModule: ehWasm, mainWorker: ehWorker },
    coi: { mainModule: ehWasm, mainWorker: ehWorker },
  };
  let bundle = await duckdb.selectBundle(localBundles);
  if (!bundle || !bundle.mainModule) bundle = localBundles.eh;

  // Brotli 解压（可选）
  const wasmUrl = bundle.mainModule;
  const wasmBrUrl = wasmUrl + '.br';
  const hasDecompressStream = typeof DecompressionStream !== 'undefined';
  let effectiveWasmUrl = wasmUrl;
  if (hasDecompressStream) {
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

  // Worker 脚本：优先 blob: importScripts，失败时回退到直接 new Worker
  const workerScript = `importScripts("${bundle.mainWorker}");`;
  let worker;
  try {
    const workerBlobUrl = URL.createObjectURL(new Blob([workerScript], { type: 'text/javascript' }));
    worker = new Worker(workerBlobUrl);
  } catch (e) {
    console.warn('[db] blob worker failed, using direct URL:', e.message);
    worker = new Worker(bundle.mainWorker);
  }

  let logger = null;
  try { logger = new duckdb.ConsoleLogger(); } catch (_) { logger = null; }

  DB = new duckdb.AsyncDuckDB(logger, worker);
  await DB.instantiate(bundle.mainModule, bundle.prelude);

  if (effectiveWasmUrl.startsWith('blob:')) URL.revokeObjectURL(effectiveWasmUrl);

  log('正在装载本体论数据表…');
  CONN = await DB.connect();

  // 探测可用的 register API（都在 DB 上，不在 CONN 上）
  const hasBuffer = typeof DB.registerFileBuffer === 'function';
  const hasFileURL = typeof DB.registerFileURL === 'function';
  const hasFileText = typeof DB.registerFileText === 'function';
  const hasCopyFile = typeof DB.copyFileToBuffer === 'function';
  console.info(`[db] DuckDB DB-side APIs: registerFileBuffer=${hasBuffer} registerFileURL=${hasFileURL} registerFileText=${hasFileText} copyFileToBuffer=${hasCopyFile}`);

  // 逐张下载并按可用 API 注册到 DuckDB（API 位于 DB 实例）
  let loaded = 0;
  for (const name of names) {
    const url = assetUrl(`data/${name}.parquet`);
    const resp = await fetch(url, { cache: 'force-cache' });
    if (!resp.ok) throw new Error(`数据表下载失败：${name}.parquet (HTTP ${resp.status})`);
    const buf = await resp.arrayBuffer();
    const key = `mem:///${name}.parquet`;
    let tableReady = false;
    let modeUsed = '';

    // 方式 1：registerFileBuffer（DuckDB 1.29+ 标准路径）
    if (!tableReady && hasBuffer) {
      try {
        await DB.registerFileBuffer(key, new Uint8Array(buf));
        tableReady = await tryCreateTable(name, key);
        if (tableReady) modeUsed = 'registerFileBuffer';
      } catch (e) { console.warn(`[db] registerFileBuffer ${key} 失败: ${e.message}`); }
    }
    // 方式 2：registerFileURL（DuckDB 1.x：url 在前，filename 在后）
    if (!tableReady && hasFileURL) {
      try {
        const registeredName = await DB.registerFileURL(url, key);
        tableReady = await tryCreateTable(name, registeredName || key);
        if (tableReady) modeUsed = 'registerFileURL';
      } catch (e) { console.warn(`[db] registerFileURL ${key} 失败: ${e.message}`); }
    }
    // 方式 3：copyFileToBuffer + registerFileBuffer（先取 Uint8Array 再注册）
    if (!tableReady && hasCopyFile && hasBuffer) {
      try {
        const u8 = await DB.copyFileToBuffer(url);
        await DB.registerFileBuffer(key, u8);
        tableReady = await tryCreateTable(name, key);
        if (tableReady) modeUsed = 'copyFileToBuffer+registerFileBuffer';
      } catch (e) { console.warn(`[db] copyFileToBuffer ${key} 失败: ${e.message}`); }
    }
    // 方式 4：直接 CONN.query 从外部 URL 读（http/same-origin 下 Worker 可读）
    if (!tableReady) {
      try {
        await CONN.query(`CREATE OR REPLACE TABLE "${name}" AS SELECT * FROM read_parquet('${url.replace(/'/g, "''")}')`);
        tableReady = true;
        if (tableReady) modeUsed = 'direct URL read';
      } catch (e) {
        console.warn(`[db] direct URL read ${key} 失败: ${e.message}`);
      }
    }
    // 方式 5：blob: URL 兜底（同源的 blob: Worker 内不可见，仅记录日志）
    if (!tableReady) {
      try {
        const blobUrl = URL.createObjectURL(new Blob([buf], { type: 'application/octet-stream' }));
        try {
          await CONN.query(`CREATE OR REPLACE TABLE "${name}" AS SELECT * FROM read_parquet('${blobUrl}')`);
          tableReady = true;
          if (tableReady) modeUsed = 'blob: URL';
        } finally {
          URL.revokeObjectURL(blobUrl);
        }
      } catch (e) {
        console.warn(`[db] blob URL fallback ${key} 失败: ${e.message}`);
      }
    }

    if (tableReady) {
      loaded++;
      console.info(`[db] ✓ ${name} via ${modeUsed}`);
    } else {
      console.warn(`[db] ✗ ${name} 所有加载方式均失败`);
    }
  }
  console.info(`[db] 已加载 ${loaded}/${names.length} 张表`);

  TABLE_INFO = [];
  for (const name of names) {
    try {
      const r = await CONN.query(`SELECT count(*) AS c FROM "${name}"`);
      const cnt = Number(r.toArray()[0].c);
      TABLE_INFO.push({ name, rows: cnt, source: manifest[name].source || '' });
    } catch (_) {
      TABLE_INFO.push({ name, rows: 0, source: manifest[name].source || '' });
    }
  }

  READY = true;
  log('数据库就绪');
}

/** 执行 SQL，返回 { columns, rows } */
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

/** 西游记图谱总览统计 */
export async function overview() {
  const one = async (sql) => { try { return Number(await scalar(sql)) || 0; } catch (_) { return 0; } };
  return {
    editions: await one('SELECT count(*) FROM editions'),
    pages: await one('SELECT count(*) FROM pages'),
    lines: await one('SELECT count(*) FROM lines'),
    entities: await one('SELECT count(*) FROM entities'),
    relationships: await one('SELECT count(*) FROM relationships'),
    events: await one('SELECT count(*) FROM events'),
    mentions: await one('SELECT count(*) FROM mentions'),
    chapters: await one('SELECT count(*) FROM chapters'),
    annotations: await one('SELECT count(*) FROM annotations'),
  };
}
