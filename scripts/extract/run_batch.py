#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批次抽取调度器（多进程并发 + 断点续传）。

用法：
  python run_batch.py --edition 新刻全像批评西游记 --workers 3
  python run_batch.py --edition shidetang --source pdf --pdf <path>
  python run_batch.py --all --workers 4
"""
import os, sys, json, time, argparse, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SENSENOVA_API_KEY", "sk-MUdQGuADpncGwjHHPSjLAqWFTlnZUfUI")

from concurrent.futures import ProcessPoolExecutor, as_completed
from schema import EDITIONS

ROOT = r"f:\src\The-Journey-to-the-West\book\scans"
OUT_ROOT = r"f:\src\The-Journey-to-the-West\book\extract"
LOG_DIR = os.path.join(OUT_ROOT, "_logs")
os.makedirs(LOG_DIR, exist_ok=True)

SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "extract_page.py"))


def list_images(edition_dir):
    d = os.path.join(ROOT, edition_dir)
    if not os.path.isdir(d):
        return []
    files = []
    for ext in ("*.jpg", "*.png", "*.tif", "*.tiff", "*.webp"):
        files.extend(glob.glob(os.path.join(d, ext)))
    files.sort()
    return files


def run_one(edition_dir, image_path, page_no, log_dir):
    """用子进程调 extract_page.py，独立进程避免 curl.exe 并发写坏共享状态。"""
    out_path = os.path.join(OUT_ROOT, edition_dir, f"p{page_no:05d}.jsonld")
    if os.path.exists(out_path):
        return {"status": "skip", "page": page_no}

    log_path = os.path.join(log_dir, f"{edition_dir}_p{page_no:05d}.log")
    env = os.environ.copy()
    env["SENSENOVA_API_KEY"] = os.environ.get("SENSENOVA_API_KEY", "")
    cmd = ["python", SCRIPT, image_path, "--edition-dir", edition_dir]
    t0 = time.time()
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT,
                               env=env, timeout=600, text=True, encoding="utf-8")
        dt = time.time() - t0
        ok = os.path.exists(out_path)
        return {"status": "ok" if ok else "fail", "page": page_no, "dt": round(dt, 1),
                "rc": r.returncode}
    except Exception as e:
        return {"status": "err", "page": page_no, "err": str(e), "dt": round(time.time()-t0, 1)}


def process_edition(edition_dir, workers=2, limit=None, log_suffix=""):
    images = list_images(edition_dir)
    if not images:
        print(f"[WARN] 目录无图片: {edition_dir}")
        return
    print(f"[EDITION] {edition_dir}  页数={len(images)}  workers={workers}")
    tasks = []
    for img in images[:limit]:
        import re
        m = re.search(r"(\d+)", os.path.basename(img))
        page_no = int(m.group(1)) if m else 0
        tasks.append((edition_dir, img, page_no))

    log_dir = os.path.join(LOG_DIR, edition_dir)
    os.makedirs(log_dir, exist_ok=True)

    done = 0
    ok = fail = skip = err = 0
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one, e, img, p, log_dir) for (e, img, p) in tasks]
        for fut in as_completed(futures):
            r = fut.result()
            done += 1
            if r["status"] == "ok":
                ok += 1
            elif r["status"] == "fail":
                fail += 1
            elif r["status"] == "err":
                err += 1
            elif r["status"] == "skip":
                skip += 1
            if done % 5 == 0 or done == len(tasks):
                el = time.time() - t0
                rate = done / el if el > 0 else 0
                print(f"  [{done}/{len(tasks)}] ok={ok} fail={fail} skip={skip} err={err}  {el:.0f}s  {rate*60:.1f}页/分钟")

    total = time.time() - t0
    print(f"[DONE] {edition_dir}  {done}页 in {total:.0f}s  ok={ok} fail={fail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", default=None, help="书格目录名（书格/大奇书/李评本等）")
    ap.add_argument("--all", action="store_true", help="跑所有已知版本目录")
    ap.add_argument("--workers", type=int, default=2, help="并发进程数")
    ap.add_argument("--limit", type=int, default=None, help="每版本限制页数（试跑用）")
    args = ap.parse_args()

    if args.edition:
        process_edition(args.edition, args.workers, args.limit)
    elif args.all:
        for ed in sorted(EDITIONS.keys()):
            process_edition(ed, args.workers, args.limit)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
