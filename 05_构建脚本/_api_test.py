"""API 连通性测试 + 单行改写样例"""
import os, sys, json, urllib.request, urllib.error

API_KEY = os.environ.get('SENSENOVA_API_KEY', 'sk-MUdQGuADpncGwjHHPSjLAqWFTlnZUfUI')
URL = 'https://token.sensenova.cn/v1/chat/completions'

def chat(messages, temperature=0.3, max_tokens=2048):
    body = {
        'model': 'sensenova-6.8-flash-lite',
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    req = urllib.request.Request(URL,
        data=json.dumps(body).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json',
        }, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'__error__': e.code, '__body__': e.read().decode('utf-8','replace')[:500]}

# 测试 1: 简单 hello
print('== Test 1: Hello ==')
r = chat([{'role':'user','content':'Say "OK" only.'}])
print(json.dumps(r, ensure_ascii=False)[:400])

# 测试 2: 单行改写
print('\n== Test 2: 单行改写 ==')
sample = '且不言他四眾脫身，隨金剛駕風而起。卻說陳家莊救生寺內多人，天曉起來，仍治果餚。'
sys_prompt = """你是《西游记》白话文改写助手。任务：把一段古白话改写为当代书面白话。
规则：
1. 完整保留原文所有信息，不增删情节、对话、描写。
2. 保留所有专有名词与称谓原样（如：悟空、八戒、沙僧、唐僧、师父、金箍棒、金毛狮怪、九头狮子、玄帝、黄丝帐、纳锦背心等）。
3. 对话引号用中文双引号 " " 替换原文的 「 」 或 " "。
4. 去掉文言虚词：却、卻、却/卻/却、甚、甚么、甚麼、如何、不曾、但只、卻是、端坐、化齋等。
5. 语气控制为当代书面白话，不做过度口语化，不出现网络用语。
6. 不添加现代解释性内容。不输出任何解释或前后缀，只输出改写后的文本本身。
7. 遇到诗句/韵文段落（以冒号开头）仍保留原句式和意象。"""
user_prompt = f'原文：{sample}\n改写：'
r = chat([{'role':'system','content':sys_prompt},{'role':'user','content':user_prompt}])
if '__error__' in r:
    print('ERROR:', r)
else:
    print('response:', json.dumps(r, ensure_ascii=False)[:1200])
