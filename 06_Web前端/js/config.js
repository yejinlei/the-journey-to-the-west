/* ============================================================
   config.js —— 西游记 Agent · 访问者本地配置
   任何 Key 都不会离开访问者的浏览器。
   ============================================================ */

const STORAGE_KEY = 'jtw_kg_config_v1';

export const DEFAULTS = {
  baseUrl: 'https://openrouter.ai/api/v1',
  apiKey: '',
  model: 'openai/gpt-4o-mini',
  temperature: 0.2,
};

export const PROVIDER_PRESETS = [
  {
    id: 'openrouter',
    label: 'OpenRouter（推荐｜官方支持浏览器跨域）',
    baseUrl: 'https://openrouter.ai/api/v1',
    model: 'openai/gpt-4o-mini',
    models: ['openai/gpt-4o-mini', 'deepseek/deepseek-chat', 'anthropic/claude-3.5-sonnet', 'google/gemini-flash-1.5'],
    applyUrl: 'https://openrouter.ai/keys',
  },
  {
    id: 'siliconflow',
    label: '硅基流动 SiliconFlow（国内）',
    baseUrl: 'https://api.siliconflow.cn/v1',
    model: 'Qwen/Qwen2.5-7B-Instruct',
    models: ['Qwen/Qwen2.5-7B-Instruct', 'deepseek-ai/DeepSeek-V3', 'Qwen/Qwen2.5-72B-Instruct'],
    applyUrl: 'https://cloud.siliconflow.cn/account/ak',
  },
  {
    id: 'deepseek',
    label: 'DeepSeek 官方',
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    applyUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    id: 'custom',
    label: '自定义（兼容 OpenAI 接口 / 自建中转）',
    baseUrl: '',
    model: '',
    models: [],
    applyUrl: '',
  },
];

let cached = null;

export function loadConfig() {
  if (cached) return cached;
  let stored = {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) stored = JSON.parse(raw) || {};
  } catch (e) { try { console.warn('[config] read fail', e); } catch (_) {} }
  cached = { ...DEFAULTS, ...stored };
  return cached;
}

export function saveConfig(patch) {
  const next = { ...loadConfig(), ...patch };
  cached = next;
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch (e) {}
  return next;
}

export function clearConfig() {
  cached = { ...DEFAULTS };
  try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
  return cached;
}

/** 是否已配置可用的对话模型 */
export function hasLLM(cfg) {
  const c = cfg || loadConfig();
  return Boolean(c.baseUrl && c.apiKey && c.model);
}

export function normalizeBaseUrl(url) {
  let u = String(url || '').trim().replace(/\/+$/, '');
  if (!u) return '';
  if (!/^https?:\/\//i.test(u)) u = 'https://' + u;
  return u;
}

export function mixedContentWarning(baseUrl) {
  const u = normalizeBaseUrl(baseUrl);
  if (u && location.protocol === 'https:' && /^http:\/\//i.test(u)) {
    return '⚠️ 当前页面是 HTTPS，浏览器会拦截对 http:// 接口的调用。请把接口改成 https://；若自建服务只开 HTTP，需加 HTTPS 反向代理。';
  }
  return null;
}
