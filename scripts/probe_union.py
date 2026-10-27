# -*- coding: utf-8 -*-
# 全量探测: chnCode -> dispatcher模板 -> entry 302 -> unionUrl
import socket, re, json, time
from concurrent.futures import ThreadPoolExecutor

BASE = 'F:/AK50/06_系统快照/盒子/cap/'
disp_path = open(BASE + 'disp_path.txt').read().strip()          # /gitv_live/<cid>/<cid>.m3u8?...
m3u8_url = open(BASE + 'm3u8_url.txt').read().strip()             # 带认证的播放 URL
q = m3u8_url.split('?', 1)[1]
p = dict(kv.split('=', 1) for kv in q.split('&') if '=' in kv)
AUTH = 'UserName=%s&MAC=%s&OTTUserToken=%s&accountinfo=%s' % (
    p['UserName'], p['MAC'], p['OTTUserToken'], p['accountinfo'])

j = json.load(open(BASE + 'chnssl.json', encoding='utf8'))
codes = [d['chnCode'] for d in j['data']]

def http_get(host, port, path, timeout=15):
    try:
        s = socket.create_connection((host, port), timeout); s.settimeout(timeout)
        s.sendall(('GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: okhttp/3.8.1\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n' % (path, host)).encode())
        d = b''
        while True:
            try:
                c = s.recv(32768)
                if not c: break
                d += c
                if len(d) > 300000: break
            except Exception: break
        s.close()
        return d.decode('utf8', 'ignore')
    except Exception as e:
        return 'ERR ' + str(e)

def probe(code):
    # 1. dispatcher
    dp = re.sub(r'/gitv_live/[^/]+/[^/]+\.m3u8', '/gitv_live/%s/%s.m3u8' % (code, code), disp_path)
    t = http_get('jscmcc-livod.dispatcher.gitv.tv', 80, dp)
    m = re.search(r'"url"\s*:\s*"([^"]+)"', t)
    if not m:
        return code, 'NO_TEMPLATE', t[:80]
    tmpl = m.group(1).replace('\\/', '/').replace('%s', '183.207.249.71')
    if tmpl.startswith('http://'): tmpl = tmpl[7:]
    mm = re.match(r'([^/:]+)(/.*)', tmpl)
    if not mm:
        return code, 'BAD_TMPL', tmpl[:80]
    host, path = mm.group(1), mm.group(2)
    # 2. entry 302
    t2 = http_get(host, 80, path + '?' + AUTH)
    loc = re.search(r'Location:\s*(\S+)', t2)
    if not loc:
        return code, 'NO_302', t2.split('\r\n')[0] + ' | ' + t2[:120].replace('\r\n', ' ')
    nu = loc.group(1)
    uu = re.search(r'unionUrl=([^&]+)', nu)
    pltv = re.search(r'/PLTV/(\d+)/(\d+)/(\d+)/', nu)
    return code, (pltv.group(3) if pltv else '?'), (uu.group(1) if uu else nu[:100])

res = []
with ThreadPoolExecutor(8) as ex:
    for r in ex.map(probe, codes):
        res.append(r)
        print('%-40s PLTV=%-12s union=%s' % r, flush=True)

json.dump(res, open(BASE + 'union_map.json', 'w'), ensure_ascii=False, indent=1)
print('OK, saved union_map.json')
