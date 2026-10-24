"""
西游记古本 2538 行全量白话文改写脚本
- 分批处理、断点续跑、失败重试、4 并发限流
- 输出：_rewrite_progress.jsonl（每行一条 JSON，含 page/line/original/rewritten/status）
- 输出：_rewrite_stats.json（统计：成功/失败/耗时/长度分布）
"""
import os, sys, json, time, threading, queue, traceback, re
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from opencc import OpenCC
    _opencc_t2s = OpenCC('t2s')
    def _t2s(text):
        try:
            return _opencc_t2s.convert(text)
        except Exception:
            return text
except ImportError:
    try:
        import opencc
        _opencc_conv = opencc.OpenCC('t2s')
        def _t2s(text):
            try:
                return _opencc_conv(text)
            except Exception:
                return text
    except Exception:
        def _t2s(text):
            return text  # opencc 不可用，退回原样

# 备用手工映射表：常见繁体→简体（在 opencc 不可用时兜底）
_MANUAL_T2S = {
    '為':'为','個':'个','與':'与','說':'说','麼':'么','後':'后','時間':'时间','樣':'样',
    '這':'这','那':'那','還':'还','過':'过','發':'发','變':'变','讓':'让','問':'问','頭':'头',
    '話':'话','裡':'里','對':'对','來':'来','讀':'读','經':'经','書':'书','寫':'写','畫':'画',
    '龍':'龙','門':'门','會':'会','當':'当','機':'机','點':'点','寶':'宝','靈':'灵','華':'华',
    '鳳':'凤','師':'师','語':'语','學':'学','長':'长','時':'时','東':'东','國':'国','邊':'边',
    '見':'见','聽':'听','話':'话','語':'语','見':'见','聽':'听',
    '實':'实','實':'实','實':'实','實':'实','實':'实','見':'见',
    '為':'为','個':'个','與':'与','說':'说','麼':'么','後':'后','樣':'样',
    '這':'这','還':'还','過':'过','發':'发','變':'变','讓':'让','問':'问','頭':'头',
    '話':'话','裡':'里','對':'对','來':'来','讀':'读','經':'经','書':'书','寫':'写','畫':'画',
    '龍':'龙','門':'门','會':'会','當':'当','機':'机','點':'点','寶':'宝','靈':'灵','華':'华',
    '師':'师','語':'语','學':'学','長':'长','時':'时','東':'东','國':'国','邊':'边',
    '見':'见','聽':'听','實':'实',
}

def to_simplified(text):
    """统一转简体：优先 OpenCC，兜底手工映射。"""
    if not text:
        return text
    result = _t2s(text)
    # OpenCC 未处理到的字符，用手工映射补一遍
    return ''.join(_MANUAL_T2S.get(c, c) for c in result)

API_KEY = os.environ.get('SENSENOVA_API_KEY', 'sk-RT5C6gTnhWqasXT6Yg4PMcfOE8s4wYca')
URL = 'https://token.sensenova.cn/v1/chat/completions'
MODEL = os.environ.get('REWRITE_MODEL', 'deepseek-flash')

PROGRESS_PATH = r'_rewrite_progress.jsonl'
STATS_PATH = r'_rewrite_stats.json'
READ_JSON = r'docs/data/pages/read.json'

SYS_PROMPT = """你是《西游记》白话文改写助手。把一段古白话改写为通俗易懂的当代书面白话。

规则：
1. 完整保留原文所有信息，不增删情节、对话、描写。原文末尾的内容必须完整改写到位，禁止截断。
2. 保留所有专有名词与称谓原样（悟空、八戒、沙僧、唐僧、师父、金箍棒、玄帝等）。
3. 对话引号统一用中文双引号 "" 替换 「」 或其他引号。
4. 去掉文言虚词：卻、甚、甚么、如何、不曾、但只、端坐、化齋、矣、之、乃、皆、俱、即、遂、夫、乎、者、也、則、無、復、何、甚、蓋。
5. 使用现代汉语语法和常用动词，不用文言句式。
6. 输出全部使用简体字，禁止繁体字残留。特别注意：師→师、問→问、為→为、说→说、這→这、個→个、裡→里、實→实、語→语、學→学、長→长、書→书、時→时、東→东、國→国、邊→边、來→来、過→过、後→后、話→话、見→见、聽→听、讀→读、畫→画、寫→写、龍→龙、門→门、發→发、會→会、當→当、頭→头、對→对、機→机、點→点、經→经、寶→宝、靈→灵、華→华、鳳→凤。
7. 通俗易懂的当代书面白话，不口语化，不添加现代解释性内容。
8. 遇到诗句/韵文段落，用现代白话直译成通顺的现代汉语。
9. 只输出改写文本本身，不输出任何说明、检查清单或思考过程。
"""

SYS_REVIEW = """你是《西游记》改写质量审校员。请检查下面这段改写文本，对照原文做以下修正：

必须修正的问题：
1. 繁体字残留：任何繁体字（師問為說這裡實語學長書時東國邊來過後話見聽讀經書寫畫龍門發會當頭對機點寶靈華鳳等）立即替换成简体。
2. 内容截断：如果改写内容比原文末尾少了内容，把丢失的部分按上下文补写回来。
3. 引号：非 "" 中文双引号的引号改成 ""。
4. 专有名词被改动：恢复原样。
5. 出现原文没有的现代解释或评论：删除。

保持不变的：
- 专有名词原样保留（悟空、八戒、师父等）
- 整体风格和句意忠实于原文

原文：
{original}

待审校改写：
{rewritten}

只输出修正后的完整文本，不输出任何说明、清单或对比过程。"""

def call_api(text, retry=3, timeout=120, use_review=False, original=None):
    """调用 API，返回 (rewritten_text, error_msg)。error_msg 为 None 表示成功。

    use_review=True 时走 SYS_REVIEW 审校模式：text 是待审校的改写，original 是原文。
    """
    global _last_api_ts
    # 主动节流：任意时刻相邻两次 API 请求之间至少间隔 2 秒（1 worker 用）
    with _api_lock:
        now = time.time()
        gap = _MIN_API_INTERVAL - (now - _last_api_ts)
        if gap > 0:
            time.sleep(gap)
        _last_api_ts = time.time()
    if use_review:
        user_prompt = SYS_REVIEW.format(original=original or text, rewritten=text)
        system_prompt = '你是《西游记》改写审校员，只做质量修正，不添加新内容。'
    else:
        user_prompt = f'原文：{text}\n改写：'
        system_prompt = SYS_PROMPT
    # 动态 max_tokens：按原文长度 2 倍 + 1024 缓冲（官方推荐 2048-4096）
    max_tokens = min(4096, max(2048, int(len(text) * 2) + 1024))
    body = json.dumps({
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 1.0,
        'max_tokens': max_tokens,
    }).encode('utf-8')
    last_err = None
    for attempt in range(retry):
        req = urllib.request.Request(URL, data=body,
            headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
            method='POST')
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode('utf-8'))
            content = data.get('choices',[{}])[0].get('message',{}).get('content','')
            content = content.strip()
            # 去掉模型可能生成的 markdown 代码围栏
            if content.startswith('```'):
                content = content.split('\n',1)[-1] if '\n' in content else ''
                if content.endswith('```'):
                    content = content.rsplit('```',1)[0]
                content = content.strip()
            if content:
                return content, None
            last_err = 'empty content'
            # empty content 往往是限流/被拒的静默信号，加大退避
            time.sleep(4 + 3 * attempt)
        except urllib.error.HTTPError as e:
            body_err = e.read().decode('utf-8','replace')[:300]
            last_err = f'HTTP {e.code}: {body_err}'
            if e.code == 429:
                # 指数退避，上限 90 秒
                import random
                base = min(90, 15 * (2 ** attempt))
                time.sleep(base + random.uniform(0, 3))
                continue
            time.sleep(3 + 2 * attempt)
        except Exception as e:
            last_err = f'{type(e).__name__}: {str(e)[:200]}'
            time.sleep(3 + 2 * attempt)
    return None, last_err


def is_skip_line(line_obj):
    """是否跳过改写：章节标题行、极短行、纯韵文段落开头"""
    ft = line_obj.get('form_type', '')
    text = line_obj.get('text', '') or ''
    if ft == 'title':
        return True
    # L0 通常是章节标记
    if line_obj.get('line_idx', 1) == 0:
        return True
    # 极短行（<=6 字）不改写
    stripped = text.strip()
    if len(stripped) <= 6:
        return True
    return False


def chunk_text(text, max_chunk=250):
    """把长文按段落/换行/标点切成 chunk，每个 chunk 长度 <= max_chunk。
    deepseek-flash 单次改写 200 字长文稳定输出 ~230 字。"""
    if len(text) <= max_chunk:
        return [text]
    parts = []
    buf = ''
    # 按 \n 分段，长段落按强标点切分
    for para in text.split('\n'):
        if not para.strip():
            continue
        if len(buf) + len(para) + 1 <= max_chunk:
            buf += ('\n' if buf else '') + para
            continue
        # 段落本身太长，按标点切
        if len(para) > max_chunk:
            if buf:
                parts.append(buf)
                buf = ''
            # 按句号类切分（含中英文标点）
            segs = re.split(r'(?<=[。；！？：！\?\n])', para)
            sub_buf = ''
            for seg in segs:
                if not seg:
                    continue
                # 如果单个 seg 还超长（罕见），按句号再切
                if len(seg) > max_chunk:
                    if sub_buf:
                        parts.append(sub_buf)
                        sub_buf = ''
                    # 强制硬切
                    for i in range(0, len(seg), max_chunk):
                        parts.append(seg[i:i+max_chunk])
                    continue
                if len(sub_buf) + len(seg) <= max_chunk:
                    sub_buf += seg
                else:
                    if sub_buf:
                        parts.append(sub_buf)
                    sub_buf = seg
            if sub_buf:
                parts.append(sub_buf)
        else:
            if buf:
                parts.append(buf)
            buf = para
    if buf:
        parts.append(buf)
    return [p for p in parts if p.strip()]


def rewrite_long(text):
    """超长文本分块改写后拼接。单块直接一次调用。"""
    chunks = chunk_text(text)
    if len(chunks) == 1:
        return call_api(text)
    results = []
    for i, c in enumerate(chunks):
        out, err = call_api(c)
        if out is None:
            out = c  # 失败保留原文
        results.append(out)
    return '\n'.join(results), None


def normalize_quotes(text):
    """「」 → "" ；' ' → "" ；保留原本的 "" """
    if not text:
        return text
    # 「」 → " 配对替换
    out = []
    for ch in text:
        if ch == '「':
            out.append('"')
        elif ch == '」':
            out.append('"')
        elif ch == '『':
            out.append('"')
        elif ch == '』':
            out.append('"')
        else:
            out.append(ch)
    return ''.join(out)


def validate_rewrite(original, rewritten):
    """长度/质量校验：返回 (ok, reason)"""
    if not rewritten or not rewritten.strip():
        return False, 'empty'
    orig = original.strip()
    rwt = rewritten.strip()
    orig_len = len(orig)
    rwt_len = len(rwt)
    if rwt_len < orig_len * 0.5:
        return False, f'too_short:{rwt_len}<{orig_len}*0.5'
    if rwt_len > orig_len * 4.0:
        return False, f'too_long:{rwt_len}>{orig_len}*4.0'
    # 繁体字检测（更严格的常见繁体清单，排除简体字避免误报）
    trad_chars = '為個與說麼後時間樣這那還過發變讓問頭話裡對來讀經書寫畫龍門發會當師語問這個說裡頭話語讀經書寫畫龍門發會當機點對過後話'
    trad_chars_set = set(trad_chars) - set('个与说么后时间样这那还过发变让问头话里对来读经书写画龙门发会对师语读经书写画龙门发会对机点对话')
    trad_count = sum(1 for c in rwt if c in trad_chars_set)
    if orig_len > 20 and trad_count > 2:
        return False, f'trad_chars:{trad_count}'
    # 截断检测：原文后半段关键词若被丢失，判定为截断
    # 取原文后半段的 5 个中文字符（间隔取样），若都未出现在改写里则视为截断
    if orig_len > 60:
        tail = orig[orig_len * 2 // 3:]
        # 提取原文尾部连续出现的独特字词（每 5 字一段，最多 3 段）
        sample_words = []
        for i in range(0, min(len(tail), 30), 5):
            w = tail[i:i+5]
            if len(w) >= 4 and not any(ch in '"「」\'.,;:！？。，；：' for ch in w):
                sample_words.append(w)
        if sample_words:
            missing = sum(1 for w in sample_words if w not in rwt)
            if missing >= 2 and len(sample_words) >= 2:
                return False, f'truncated:missing_{missing}/{len(sample_words)}'
    return True, 'ok'


def load_read_lines():
    with open(READ_JSON, encoding='utf-8') as f:
        d = json.load(f)
    lines = [l for l in d['lines'] if l.get('edition') == 'gubao' and (l.get('page_no') or 0) > 0]
    return lines


def load_done_keys():
    """从 progress jsonl 加载已完成的 (page, line_idx) 集合，只算 ok/skipped。
    failed/fallback 不算 done，下次运行会重试。
    """
    done = set()
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                    if rec.get('status') in ('ok', 'skipped'):
                        done.add((rec['page'], rec['line']))
                except Exception:
                    pass
    return done


LOCK = threading.Lock()
PROGRESS_F = open(PROGRESS_PATH, 'a', encoding='utf-8')

_api_lock = threading.Lock()
_last_api_ts = 0.0
_MIN_API_INTERVAL = 1.5  # 秒，每次 API 请求之间的最小间隔

def record(rec):
    with LOCK:
        PROGRESS_F.write(json.dumps(rec, ensure_ascii=False) + '\n')
        PROGRESS_F.flush()


def worker(item):
    page, line_idx, original, form_type = item[0], item[1], item[2], item[3] if len(item) > 3 else ''
    key = (page, line_idx)

    if is_skip_line({'line_idx': line_idx, 'form_type': form_type, 'text': original}):
        record({'page': page, 'line': line_idx, 'original': original,
                'rewritten': original, 'status': 'skipped', 'reason': 'skip'})
        return {'status': 'skipped'}

    rewritten, err = rewrite_long(original)
    if rewritten is None:
        record({'page': page, 'line': line_idx, 'original': original,
                'rewritten': original, 'status': 'failed', 'reason': err})
        return {'status': 'failed', 'err': err}

    rewritten = normalize_quotes(rewritten)
    # 后处理：统一转简体（OpenCC），彻底清除繁体残留
    rewritten = to_simplified(rewritten)
    ok, reason = validate_rewrite(original, rewritten)
    if not ok:
        # 重试一次（换更保守的 prompt）
        rewritten2, err2 = call_api(original + '\n(严格按规则1-8改写，不要增删内容，只输出改写文本)')
        if rewritten2:
            rewritten2 = normalize_quotes(rewritten2)
            rewritten2 = to_simplified(rewritten2)
            ok2, reason2 = validate_rewrite(original, rewritten2)
            if ok2:
                rewritten = rewritten2
                reason = 'ok_after_retry'
            else:
                reason = reason + ' | retry: ' + reason2

    if ok:
        record({'page': page, 'line': line_idx, 'original': original,
                'rewritten': rewritten, 'status': 'ok', 'reason': reason})
        return {'status': 'ok'}
    else:
        # 回退：保存转简后的原文，确保 text_zh 字段始终是简体
        record({'page': page, 'line': line_idx, 'original': original,
                'rewritten': to_simplified(original), 'status': 'fallback', 'reason': reason})
        return {'status': 'fallback', 'reason': reason}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='只处理前 N 行（0=全部）')
    ap.add_argument('--pages', default='', help='只处理这些页码，逗号分隔，如 "1,2,3"')
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()

    print('Loading read.json ...')
    lines = load_read_lines()
    print(f'  gubao lines: {len(lines)}')

    if args.pages:
        wanted = set(int(x) for x in args.pages.split(',') if x.strip())
        lines = [l for l in lines if l.get('page_no') in wanted]
        print(f'  after page filter: {len(lines)}')

    done = load_done_keys()
    print(f'  already done: {len(done)}')

    tasks = []
    for l in lines:
        key = (l.get('page_no'), l.get('line_idx'))
        if key in done:
            continue
        tasks.append((key[0], key[1], l.get('text',''), l.get('form_type','')))

    print(f'  to process: {len(tasks)}')
    if not tasks:
        print('All done. Computing stats.')
        compute_stats()
        return

    t0 = time.time()
    ok_count = fail_count = skip_count = fb_count = 0
    stats_lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(worker, t): t for t in tasks}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                r = fut.result()
                with stats_lock:
                    if r['status'] == 'ok':
                        ok_count += 1
                    elif r['status'] == 'skipped':
                        skip_count += 1
                    elif r['status'] == 'fallback':
                        fb_count += 1
                    else:
                        fail_count += 1
                if i % 20 == 0:
                    elapsed = time.time() - t0
                    print(f'  [{i}/{len(tasks)}] ok={ok_count} skip={skip_count} fb={fb_count} fail={fail_count} t={elapsed:.0f}s')
            except Exception as e:
                fail_count += 1
                print(f'  EXCEPTION: {e}')

    PROGRESS_F.close()
    elapsed = time.time() - t0
    print(f'\nDONE in {elapsed:.1f}s')
    print(f'  ok={ok_count} skip={skip_count} fallback={fb_count} failed={fail_count}')

    compute_stats()


def load_last_records():
    """加载 progress，(page, line) 去重后保留最后一条"""
    recs = {}
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    r = json.loads(ln)
                    recs[(r['page'], r['line'])] = r
                except Exception:
                    pass
    return list(recs.values())


def compute_stats():
    stats = {'total': 0, 'ok': 0, 'skipped': 0, 'fallback': 0, 'failed': 0,
             'length_ratio_p50': 0, 'length_ratio_p90': 0, 'length_ratio_max': 0,
             'by_page': {}}
    ratios = []
    records = load_last_records()
    for rec in records:
        stats['total'] += 1
        stats[rec['status']] += 1
        p = rec['page']
        by = stats['by_page'].setdefault(p, {'total':0,'ok':0,'fallback':0,'failed':0,'skipped':0})
        by['total'] += 1
        by[rec['status']] += 1
        if rec['status'] == 'ok':
            o = len(rec['original'])
            r = len(rec['rewritten'])
            if o > 0:
                ratios.append(r/o)
    if ratios:
        ratios.sort()
        stats['length_ratio_p50'] = round(ratios[len(ratios)//2], 3)
        stats['length_ratio_p90'] = round(ratios[int(len(ratios)*0.9)], 3)
        stats['length_ratio_max'] = round(ratios[-1], 3)
    with open(STATS_PATH, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f'Stats written to {STATS_PATH}')
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
