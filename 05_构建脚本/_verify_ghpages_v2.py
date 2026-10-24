"""verify gh-pages"""
import urllib.request, json, re

BASE = 'https://raw.githubusercontent.com/yejinlei/the-journey-to-the-west/gh-pages'

def get(path):
    req = urllib.request.Request(f'{BASE}/{path}', headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')

print('== gh-pages/data/pages/read.json ==')
txt = get('data/pages/read.json')
d = json.loads(txt)
lines = d.get('lines', [])
gubao = [l for l in lines if l.get('edition') == 'gubao']
zh = [l for l in gubao if l.get('text_zh')]
print('  gubao lines:', len(gubao), 'with text_zh:', len(zh))
if gubao:
    s = next((l for l in gubao if l.get('text_zh')), gubao[0])
    print('  sample text_zh[:80] =', repr((s.get('text_zh') or '')[:80]))

print('\n== gh-pages/sw.js CACHE ==')
sw = get('sw.js')
m = re.search(r"CACHE\s*=\s*'([^']+)'", sw)
print('  CACHE =', m.group(1) if m else '???')

print('\n== gh-pages/read.html ==')
html = get('read.html')
print('  size:', len(html))
for key in ['baiMode', 'useBai', 'jtw:toggle', 'text_zh', 'toggle.js?v=']:
    idx = html.find(key)
    print('  ' + repr(key) + ':', 'FOUND @' + str(idx) if idx >= 0 else 'MISSING')

print('\n== gh-pages/assets/toggle.js ==')
tj = get('assets/toggle.js')
print('  size:', len(tj))
for key in ["'w'", 'text_zh', 'JTW_TOGGLE', 'dispatchEvent']:
    idx = tj.find(key)
    print('  ' + repr(key) + ':', 'FOUND @' + str(idx) if idx >= 0 else 'MISSING')

print('\n== gh-pages/js/page.js v= bump ==')
js = get('js/page.js')
import re as _re
mv = _re.search(r"v=(\d+)", js)
print('  page.js? v =', mv.group(1) if mv else '???')
