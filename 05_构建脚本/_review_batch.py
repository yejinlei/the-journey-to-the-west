"""批审脚本：把 progress 里 status=ok 的改写按 (page, line) 分组，每批导出 CSV 供人工校对。

用法:
    python _review_batch.py --batch 1 --size 30
        → 导出 _review_batch1.csv（前 30 条待校对）
    python _review_batch.py --list
        → 列出所有批次状态（哪些已校对、哪些待校对）
    python _review_batch.py --apply _review_batch1.csv
        → 从校对后的 CSV 读回 review_status（ok/reject/edit），reject 的会删除改写

CSV 列: page, line, original, rewritten, review_status, comment
    review_status 取值: ok（校对通过）/ reject（拒绝，回退原文）/ edit（人工编辑过，用新 rewritten 覆盖）
"""
import json, csv, argparse, os, sys
from datetime import datetime

PROGRESS_PATH = r'_rewrite_progress.jsonl'
REVIEW_INDEX = r'_review_index.json'  # 记录每批的 page-line 集合与状态


def load_progress():
    recs = {}
    if not os.path.exists(PROGRESS_PATH):
        return recs
    with open(PROGRESS_PATH, encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
                recs[(d['page'], d['line'])] = d
            except Exception:
                pass
    return recs


def load_index():
    if not os.path.exists(REVIEW_INDEX):
        return {'batches': {}}
    with open(REVIEW_INDEX, encoding='utf-8') as f:
        return json.load(f)


def save_index(idx):
    with open(REVIEW_INDEX, 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)


def export_batch(batch_id, size):
    recs = load_progress()
    ok_recs = [(k, v) for k, v in recs.items() if v.get('status') == 'ok' and v.get('rewritten')]
    ok_recs.sort(key=lambda x: (x[0][0], x[0][1]))  # by page, line

    idx = load_index()
    batches = idx.setdefault('batches', {})

    # 分配批次号：跳过已存在的
    if str(batch_id) in batches:
        existing = batches[str(batch_id)]
        print(f'批次 {batch_id} 已存在（{existing.get("count")} 条，状态 {existing.get("status")}），如需重新导出请先删除')
        return
    start = (batch_id - 1) * size
    end = start + size
    batch_items = ok_recs[start:end]
    if not batch_items:
        print(f'没有待导出的记录（第 {batch_id} 批超出范围，共 {len(ok_recs)} 条 ok 记录）')
        return

    csv_path = f'_review_batch{batch_id}.csv'
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['page', 'line', 'original', 'rewritten', 'review_status', 'comment'])
        for (p, li), rec in batch_items:
            w.writerow([p, li, rec.get('original', ''), rec.get('rewritten', ''), '', ''])

    batches[str(batch_id)] = {
        'keys': [f'{p}_{li}' for p, li in [(p, li) for (p, li), _ in batch_items]],
        'count': len(batch_items),
        'status': 'pending',
        'exported_at': datetime.now().isoformat(timespec='seconds'),
    }
    save_index(idx)
    print(f'✓ 已导出 {csv_path}，共 {len(batch_items)} 条')
    print(f'  页范围: p{batch_items[0][0][0]}-p{batch_items[-1][0][0]}')
    print(f'  总待审: {len(ok_recs)} 条 ok，本批后剩 {len(ok_recs) - end} 条')


def apply_batch(batch_id):
    csv_path = f'_review_batch{batch_id}.csv'
    if not os.path.exists(csv_path):
        print(f'找不到 {csv_path}')
        return

    idx = load_index()
    batches = idx.setdefault('batches', {})
    if str(batch_id) not in batches:
        print(f'批次 {batch_id} 未在索引中注册')
        return

    # 读 CSV
    rows = []
    with open(csv_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    # 应用：写回 progress.jsonl（新文件：_rewrite_reviewed.jsonl）
    # 策略：读取原 progress，把每条按 (page,line) 匹配，reject 的直接丢弃，edit 的更新 rewritten，ok 的保留
    reviewed_path = r'_rewrite_reviewed.jsonl'
    with open(PROGRESS_PATH, encoding='utf-8') as f, open(reviewed_path, 'w', encoding='utf-8') as g:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
            except Exception:
                continue
            key = (d.get('page'), d.get('line'))
            # 找对应的 CSV 行
            csv_row = next((r for r in rows if int(r['page']) == key[0] and int(r['line']) == key[1]), None)
            if csv_row:
                status = (csv_row.get('review_status') or '').strip().lower()
                if status == 'reject':
                    continue  # 丢弃，不写入 reviewed 文件
                elif status == 'edit' and csv_row.get('rewritten'):
                    d['rewritten'] = csv_row['rewritten']
                    d['status'] = 'ok_edited'
                    d['reviewed_at'] = datetime.now().isoformat(timespec='seconds')
                elif status == 'ok':
                    d['status'] = 'ok_reviewed'
                    d['reviewed_at'] = datetime.now().isoformat(timespec='seconds')
            g.write(json.dumps(d, ensure_ascii=False) + '\n')

    batches[str(batch_id)]['status'] = 'reviewed'
    batches[str(batch_id)]['reviewed_at'] = datetime.now().isoformat(timespec='seconds')
    save_index(idx)
    print(f'✓ 已应用校对结果到 {reviewed_path}')


def list_batches():
    idx = load_index()
    batches = idx.get('batches', {})
    recs = load_progress()
    total_ok = sum(1 for v in recs.values() if v.get('status') == 'ok')
    print(f'总 ok 改写: {total_ok}')
    print(f'已导出批次数: {len(batches)}')
    for bid in sorted(batches.keys(), key=int):
        b = batches[bid]
        print(f'  批次 {bid}: {b.get("count")} 条, 状态={b.get("status")}, 导出时间={b.get("exported_at")}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', type=int, help='导出指定批次（1 起）')
    ap.add_argument('--size', type=int, default=30, help='每批条数，默认 30')
    ap.add_argument('--apply', help='应用校对后的 CSV')
    ap.add_argument('--list', action='store_true', help='列出所有批次')
    args = ap.parse_args()

    if args.list:
        list_batches()
    elif args.batch:
        export_batch(args.batch, args.size)
    elif args.apply:
        apply_batch(int(args.apply))
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
