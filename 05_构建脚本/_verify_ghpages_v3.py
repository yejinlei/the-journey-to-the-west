"""verify gh-pages via GitHub API"""
import subprocess, json, urllib.request, re, base64
TOKEN = subprocess.check_output(['gh','auth','token']).decode().strip()
API = 'https://api.github.com/repos/yejinlei/the-journey-to-the-west/contents'
def get(path):
    r = urllib.request.Request(f'{API}/{path}?ref=gh-pages', headers={'Authorization': f'token {TOKEN}','Accept':'application/vnd.github+json'})
    return json.loads(urllib.request.urlopen(r,timeout=30).read())['content']

sw = base64.b64decode(get('sw.js')).decode('utf-8')
m = re.search(r"CACHE\s*=\s*'([^']+)'", sw)
print('sw.js CACHE =', m.group(1) if m else '???')

pj = base64.b64decode(get('js/page.js')).decode('utf-8')
m = re.search(r'v=(\d+)', pj)
print('page.js v =', m.group(1) if m else '???')

rh = base64.b64decode(get('read.html')).decode('utf-8')
m = re.search(r'toggle\.js\?v=(\d+)', rh)
print('read.html toggle.js v =', m.group(1) if m else '???')
print('read.html baiMode:', 'baiMode' in rh)
print('read.html text_zh:', 'text_zh' in rh)
print('read.html jtw:toggle:', 'jtw:toggle' in rh)

rj = base64.b64decode(get('data/pages/read.json')).decode('utf-8')
d = json.loads(rj)
gubao = [l for l in d.get('lines',[]) if l.get('edition')=='gubao']
zh = [l for l in gubao if l.get('text_zh')]
print(f'read.json gubao lines={len(gubao)} with_zh={len(zh)}')
