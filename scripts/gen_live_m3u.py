#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
江苏移动(GITV) IPTV 直播源批量生成器
原理（2026-10-27 逆向 M301H-C 盒子抓包得到）：
  1) dispatcher: GET /gitv_live/<cid>/<cid>.m3u8?...token...  -> 返回 url 模板 %s/gitv/live1/<cid>/<cid>
  2) 入口 183.207.249.71: GET <模板路径>?UserName&MAC&OTTUserToken&accountinfo -> 302 到
     http://ott.mobaibox.com/PLTV/<x>/224/<频道ID>/index.m3u8?...（带同一套 auth）
  3) 该 m3u8 可直接播放（accountinfo 是账号级的，全频道通用）
用法: python gen_live_m3u.py [输出文件]
"""
import socket, re, json, sys, os, time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
CAP = 'F:/AK50/06_系统快照/盒子/cap'

# ---------- 读取抓包得到的凭据 ----------
def load_creds():
    u = open(os.path.join(CAP, 'm3u8_url.txt')).read().strip()
    q = u.split('?', 1)[1]
    p = dict(kv.split('=', 1) for kv in q.split('&') if '=' in kv)
    auth = 'UserName=%s&MAC=%s&OTTUserToken=%s&accountinfo=%s' % (
        p['UserName'], p['MAC'], p['OTTUserToken'], p['accountinfo'])
    disp = open(os.path.join(CAP, 'disp_path.txt')).read().strip()
    return auth, disp

def http_get(host, path, hosthdr=None, port=80, timeout=12):
    hh = hosthdr or host
    s = socket.create_connection((host, port), timeout)
    s.settimeout(timeout)
    s.sendall(('GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: okhttp/3.8.1\r\n'
               'Accept-Encoding: identity\r\nConnection: close\r\n\r\n' % (path, hh)).encode())
    d = b''
    while True:
        try:
            c = s.recv(16384)
            if not c: break
            d += c
            if len(d) > 300000: break
        except Exception:
            break
    try: s.close()
    except Exception: pass
    return d.decode('utf8', 'ignore')

# ---------- 频道名美化 ----------
def clean_name(cid):
    n = cid
    n = re.sub(r'^G_', '', n)
    n = re.sub(r'-HD-?\d*[kKmM]?.*$', '', n)
    n = re.sub(r'-HQ.*$', '', n)
    n = re.sub(r'-\d+M$', '', n)
    n = re.sub(r'^HD-\d+k-\d+P-', '', n)
    n = n.replace('_', '-')
    return n

# Channels.db 的中文名，用于辅助匹配
def load_db_names():
    names = []
    db = 'F:/AK50/06_系统快照/盒子/cap/Channels.db'
    if not os.path.exists(db): return names
    try:
        import sqlite3
        c = sqlite3.connect(db)
        for (no, nm) in c.execute('select no,name from ChannelsTable order by no'):
            names.append((no, nm))
    except Exception:
        pass
    return names

def match_cn(cid, dbnames):
    """用频道号/关键词匹配中文名"""
    key = clean_name(cid).upper()
    # 提取数字，如 CCTV-1 -> 1
    m = re.search(r'(\d+)', key)
    num = m.group(1) if m else None
    for (no, nm) in dbnames:
        up = nm.upper()
        if num and re.search(r'(?:^|[^0-9])%s(?:[^0-9]|$)' % re.escape(num), up):
            if ('CCTV' in key and 'CCTV' in up) or ('CCTV' not in key and 'CCTV' not in up):
                return nm
    # 关键词匹配
    for kw, cn in [('WUXIDUSHI', '无锡都市'), ('WUXI', '无锡'), ('JIANGYIN', '江阴'),
                   ('JIANGSU', '江苏'), ('NANJING', '南京'), ('CCTV', 'CCTV')]:
        if kw in key:
            for (no, nm) in dbnames:
                if cn in nm: return nm
            break
    return None

# ---------- 单频道解析 ----------
def resolve(cid, auth, disp_tpl, dbnames):
    """返回 (可用最终URL, 备注)"""
    try:
        # 1) dispatcher 拿 url 模板
        path = disp_tpl.replace('JSGD-GW-SMS-wuxidushi', cid)
        t = http_get('jscmcc-livod.dispatcher.gitv.tv', path)
        m = re.search(r'"url":"([^"]+)"', t)
        if not m:
            return None, 'dispatcher无url'
        tmpl = m.group(1).replace('\\/', '/').replace('%s', '')
        # 2) 入口拿 PLTV 路径
        t2 = http_get('183.207.249.71', tmpl + '?' + auth)
        m2 = re.search(r'Location:\s*(\S+)', t2)
        if not m2:
            return None, '入口无302'
        loc = m2.group(1)
        m3 = re.search(r'(/PLTV/\d+/\d+/\d+/index\.m3u8)', loc)
        if not m3:
            return None, '无PLTV'
        # 3) 组装最终 URL（用域名，自动调度到 CDN 节点）
        final = 'http://ott.mobaibox.com' + m3.group(1) + '?' + auth
        # 4) 验证可播
        v = http_get('223.110.242.32', m3.group(1) + '?' + auth, hosthdr='ott.mobaibox.com')
        ok = '200' in v[:20]
        return final, ('OK' if ok else 'CDN未200')
    except Exception as e:
        return None, str(e)[:40]

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'F:/AK50/07_直播源/js_cmcc_iptv.m3u'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    auth, disp = load_creds()
    dbnames = load_db_names()
    chns = json.load(open(os.path.join(CAP, 'chnssl.json'), encoding='utf8'))
    cids = [d['chnCode'] for d in chns.get('data', [])]
    print('频道数:', len(cids))
    print('auth 长度:', len(auth))

    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(resolve, c, auth, disp, dbnames): c for c in cids}
        for i, f in enumerate(futs, 1):
            cid = futs[f]
            try:
                url, note = f.result()
            except Exception as e:
                url, note = None, str(e)[:40]
            results.append((cid, url, note))
            if i % 20 == 0 or i == len(cids):
                print('  进度 %d/%d' % (i, len(cids)))

    ok = [r for r in results if r[1]]
    print('成功:', len(ok), '/', len(results))

    lines = ['#EXTM3U']
    for (cid, url, note) in results:
        if not url: continue
        cn = match_cn(cid, dbnames)
        name = cn if cn else clean_name(cid)
        lines.append('#EXTINF:-1 tvg-name="%s" ,%s' % (name, name))
        lines.append(url)
    with open(out, 'w', encoding='utf8') as f:
        f.write('\n'.join(lines) + '\n')
    print('已写入:', out)

    # 明细
    det = os.path.splitext(out)[0] + '_明细.txt'
    with open(det, 'w', encoding='utf8') as f:
        for (cid, url, note) in results:
            f.write('%-40s %-10s %s\n' % (cid, note, url or ''))
    print('明细:', det)
    # 失败列表
    fail = [(c, n) for (c, u, n) in results if not u]
    if fail:
        print('失败样例:', fail[:8])

if __name__ == '__main__':
    main()
