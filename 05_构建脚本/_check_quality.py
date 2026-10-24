import json, re, sys

trads = set('為個與說麼後時間樣還過變讓问頭話裡對來讀經書寫畫龍門會當機點寶靈華鳳師語學長東國邊見聽實麼這')

for line in open('_rewrite_progress.jsonl', encoding='utf-8'):
    d = json.loads(line)
    if d.get('status') != 'ok':
        continue
    orig = d['original']
    rew = d['rewritten']
    trad_hits = sum(1 for c in rew if c in trads)
    ratio = len(rew) / max(len(orig), 1)
    print(f"p{d['page']} L{d['line']} orig={len(orig)} rew={len(rew)} ratio={ratio:.2f} trad={trad_hits}")
    print('  O:', orig[:100].replace('\n', ' '))
    print('  R:', rew[:100].replace('\n', ' '))
    print('  R_tail:', rew[-60:].replace('\n', ' '))
    print()
