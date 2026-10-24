"""打印应用映射后仍被判为伪白话的条目，对比原文与当前 text_zh，便于进一步改写。"""
import json, re, subprocess, sys
from pathlib import Path

# 复用 _apply_baihua.py 的字典
TRAD = {
    '東':'东','龍':'龙','鳳':'凤','漢':'汉','經':'经','國':'国','書':'书','讀':'读',
    '說':'说','時':'时','後':'后','麼':'么','這':'这','們':'们','個':'个','頭':'头',
    '髮':'发','鬚':'须','見':'见','開':'开','關':'关','問':'问','題':'题','話':'话',
    '語':'语','誰':'谁','過':'过','會':'会','於':'于','為':'为','來':'来','門':'门',
    '學':'学','寫':'写','畫':'画',
}
def simp(s): return ''.join(TRAD.get(c, c) for c in s)
def norm(s): return re.sub(r'[\s，。、「」『』：；？！.,:;!?()\[\]\'"\-—…～]+','',s)
def fake(t, tz):
    a = norm(tz); b = norm(simp(t))
    if not a or not b: return False
    p = min(60, len(a), len(b))
    return sum(1 for x, y in zip(a[:p], b[:p]) if x == y) / max(p, 1) >= 0.85

d = json.loads(Path('docs/data/pages/read.json').read_text(encoding='utf-8'))
n = 0
for i, l in enumerate(d['lines']):
    if l.get('edition') != 'gubao': continue
    t = l.get('text','')
    if len(t) < 10: continue
    if not fake(t, l.get('text_zh','')): continue
    n += 1
    print(f'=== [{n}] idx={i} {l["page_id"]} ===')
    print('原文:', t)
    print('---')
    print('现zh:', l.get('text_zh',''))
    print()
