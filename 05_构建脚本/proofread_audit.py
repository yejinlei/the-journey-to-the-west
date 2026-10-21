"""
西游记古本白话文全量校对脚本（机械层）

审计维度：
  A. 覆盖率：每行 text_zh 是否非空
  B. 段数一致：源与译按 " :" 切分数目是否相同
  C. 分隔符规范：是否误用 " : "（含尾随空格）
  D. 标点统一：是否残留繁体标点（，。；：？！「」等）在非韵文段
  E. 引号规范：是否含 ASCII 双引号 " 或 直角引号 " "
  F. 字符比例：译文/原文长度比是否在合理区间（0.6-1.8）
  G. 专有名词一致性：
     - 唐僧/唐三藏/师父 是否稳定
     - 悟空/行者/大圣/悟空 是否稳定
     - 八戒/八戒/豬八戒 是否稳定
     - 沙僧/沙和尚/悟淨 是否稳定
  H. 段间内容检查：某段 source 含内容但 translation 该段为空
  I. 重复检测：translation 是否有明显重复段
"""
import json
import re
import sys
from collections import Counter, defaultdict

READ = r'f:\src\The-Journey-to-the-West\docs\data\pages\read.json'

def load():
    return json.load(open(READ, encoding='utf-8'))

def segs(s):
    # 项目约定：space-colon（含可选尾随空格）为段分隔符
    return re.split(r' : ?', s)

def is_verse_preserved(line):
    """判断该行是否属于「韵文保留繁体」类：
    - 全繁体原文（含「詩曰」/「詞曰」开头或以韵文标记结尾）
    - 章节标题（idx=0 且含"回"字）
    - text_zh == text
    """
    t = line['text']; z = line.get('text_zh', '')
    if z == t:
        return True
    if re.match(r'^.*[回章詩詞曰]', t[:20]):
        return True
    return False

def audit(path: str = None, page_range=None):
    """审计 read.json。page_range=(start,end) 只审指定页范围。"""
    rd = path or READ
    d = json.load(open(rd, encoding='utf-8'))
    g = [l for l in d['lines'] if l.get('edition') == 'gubao']
    if page_range:
        a, b = page_range
        g = [l for l in g if a <= l['page_no'] <= b]

    results = {
        'total': len(g),
        'missing': [],
        'seg_mismatch': [],
        'bad_sep': [],
        'trad_punct': [],
        'ascii_quote': [],
        'curly_quote': [],
        'ratio_outlier': [],
        'name_issues': [],
        'empty_seg': [],
        'dup_seg': [],
    }

    for l in g:
        key = f"p{l['page_no']}L{l['line_idx']}"
        t = l.get('text', '')
        z = l.get('text_zh', '')

        # A. 覆盖率
        if not z:
            results['missing'].append(key)
            continue

        # B. 段数一致
        n_t = len(segs(t)); n_z = len(segs(z))
        if n_t != n_z:
            results['seg_mismatch'].append((key, n_t, n_z))

        # C. 分隔符
        # 源文本里用 " :" 或 " :"（space-colon[+space]）
        # 译文里应保持一致：如果源含 " :" 则译也应含 " :"
        # 这里检测译文是否混入了其他分隔（如 "：" 中文冒号后无空格的段切分）
        if ' :' in z and '  :' in z.replace(': ', ' :'):
            pass  # ok
        # 检测 " : " 是否被误写为中文冒号"："（除韵文保留段外）
        if not is_verse_preserved(l):
            # 分段后检查每段是否意外使用中文冒号做段分隔
            for seg in segs(z):
                if '：' in seg and '：' == seg.strip()[:2]:
                    results['bad_sep'].append((key, seg[:50]))

        # D. 标点统一：仅对非韵文保留行检测繁体标点
        if not is_verse_preserved(l):
            for p in ['，', '。', '；', '：', '？', '！', '「', '」']:
                if p in z:
                    results['trad_punct'].append((key, p, z[:80]))
                    break

        # E. 引号
        if '"' in z:
            results['ascii_quote'].append(key)
        if '“' in z or '”' in z:
            results['curly_quote'].append(key)

        # F. 字符比例（非韵文保留行）
        if not is_verse_preserved(l) and len(t) > 20:
            r = len(z) / len(t)
            if r < 0.6 or r > 1.8:
                results['ratio_outlier'].append((key, round(r, 3), len(t), len(z)))

        # H. 空段
        t_segs = segs(t); z_segs = segs(z)
        for i, (ts, zs) in enumerate(zip(t_segs, z_segs)):
            # 若源段>20字且译段为空
            if len(ts.strip()) > 20 and not zs.strip():
                results['empty_seg'].append((key, i, ts[:60]))
                break

        # I. 重复段
        if len(z_segs) > 1:
            seen = set()
            for zs in z_segs:
                norm = zs.strip()[:80]
                if len(norm) > 10 and norm in seen:
                    results['dup_seg'].append((key, norm[:60]))
                    break
                seen.add(norm)

    return results

def audit_names(d):
    """角色名称一致性审计。"""
    g = [l for l in d['lines'] if l.get('edition') == 'gubao']

    # 定义角色同义词组（简繁并列）
    groups = {
        '唐僧': ['唐僧', '唐三藏', '三藏', '聖僧', '圣僧', '师父', '師父', '金蝉子'],
        '悟空': ['悟空', '行者', '大聖', '大圣', '孫悟空', '孙悟空', '猴王', '美猴王'],
        '八戒': ['八戒', '豬八戒', '猪八戒', '悟能', '沙僧八戒'],
        '沙僧': ['沙僧', '沙和尚', '悟淨', '悟净', '沙悟淨', '沙悟净', '流沙河'],
        '观音': ['观音', '觀音', '觀世音', '观世音'],
        '如来': ['如來', '如来'],
        '玉帝': ['玉帝', '玉皇大帝'],
        '老君': ['老君', '太上老君'],
    }

    # 统计每个角色在所有页的出现次数
    stats = {}
    for role, aliases in groups.items():
        alias_count = Counter()
        for l in g:
            z = l.get('text_zh', '')
            for a in aliases:
                c = z.count(a)
                if c:
                    alias_count[a] += c
        stats[role] = alias_count

    return stats

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--range', help='页范围 start-end，如 1-20')
    ap.add_argument('--pages', help='指定页号，逗号分隔')
    ap.add_argument('--names', action='store_true', help='只跑角色名审计')
    args = ap.parse_args()

    d = load()

    if args.names:
        n = audit_names(d)
        print('=== 角色名称一致性 ===')
        for role, alias_count in n.items():
            items = sorted(alias_count.items(), key=lambda x: -x[1])
            if not items:
                continue
            print(f'  {role}: ' + ' | '.join(f'{a}({c})' for a, c in items))
        return

    if args.range:
        a, b = args.range.split('-')
        pr = (int(a), int(b))
    elif args.pages:
        pages = [int(x) for x in args.pages.split(',')]
        pr = (min(pages), max(pages))
    else:
        pr = None

    r = audit(page_range=pr)
    n = audit_names(d)

    scope = f'[{pr[0]}-{pr[1]}]' if pr else '[全量]'
    print(f'范围 {scope}，审计行数: {r["total"]}')
    print()
    print('=== 自动审计结果 ===')
    for k in ['missing', 'seg_mismatch', 'bad_sep', 'trad_punct',
              'ascii_quote', 'curly_quote', 'ratio_outlier',
              'empty_seg', 'dup_seg']:
        c = len(r[k])
        mark = 'OK' if c == 0 else '!!'
        print(f'  [{mark}] {k}: {c}')
    print()

    for k in ['seg_mismatch', 'bad_sep', 'trad_punct', 'ascii_quote',
              'curly_quote', 'ratio_outlier', 'empty_seg', 'dup_seg', 'missing']:
        if r[k]:
            print(f'--- {k} (前 20 条) ---')
            for item in r[k][:20]:
                print(f'  {item}')
            print()

    print('=== 角色名称一致性 ===')
    for role, alias_count in n.items():
        items = sorted(alias_count.items(), key=lambda x: -x[1])
        if not items:
            continue
        print(f'  {role}: ' + ' | '.join(f'{a}({c})' for a, c in items))

if __name__ == '__main__':
    main()
