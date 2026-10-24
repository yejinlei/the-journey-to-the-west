"""验证 gh-pages 上 read.json 是否含 text_zh + toggle.js/read.html 版本"""
import urllib.request, json, re, sys

BASE = 'https://raw.githubusercontent.com/yejinlei/the-journey-to-the-west/gh-pages'

def get(path):
    req = urllib.request.Request(f'{BASE}/{path}', headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')

# 1) gh-pages 上的 read.json
print('== gh-pages/data/pages/read.json ==')
try:
    txt = get('data/pages/read.json')
    d = json.loads(txt)
    lines = d.get('lines', [])
    gubao = [l for l in lines if l.get('edition') == 'gubao']
    zh = [l for l in gubao if l.get('text_zh')]
    print(f'  gubao lines: {len(gubao)}, with text_zh: {len(zh)}')
    if gubao:
        sample = next((l for l in gubao if l.get('text_zh')), gubao[0])
        print(f"  sample L{sample.get('line_idx')} text_zh[:80] = {(sample.get('text_zh') or '')[:80]!r}")
except Exception as e:
    print(f'  ERROR: {e}')

# 2) gh-pages sw.js CACHE 版本号
print('\n== gh-pages/sw.js CACHE ==')
try:
    sw = get('sw.js')
    m = re.search(r"CACHE\s*=\s*'([^']+)'", sw)
    print(f'  CACHE = {m.group(1) if m else "???"}')
except Exception as e:
    print(f'  ERROR: {e}')

# 3) gh-pages read.html 中是否有 baiMode / useBai / jtw:toggle
print('\n== gh-pages/read.html 关键片段 ==')
try:
    html = get('read.html')
    print(f'  file size: {len(html)} bytes')
    for key in ['baiMode', 'useBai', 'jtw:toggle', 'text_zh', 'toggle.js?v=']:
        idx = html.find(key)
        print(f'  {key!r}: {"FOUND @ " + str(idx) if idx >= 0 else "MISSING"}')
except Exception as e:
    print(f'  ERROR: {e}')

# 4) gh-pages toggle.js 是否存在且含 w 模式
print('\n== gh-pages/assets/toggle.js ==')
try:
    tj = get('assets/toggle.js')
    print(f'  size: {len(tj)} bytes')
    for key in ["'w'", 'text_zh', 'JTW_TOGGLE', "dispatchEvent"]:
        idx = tj.find(key)
        print(f'  {key!r}: {"FOUND @ " + str(idx) if idx >= 0 else "MISSING"}')
except Exception as e:
    print(f'  ERROR: {e}')
