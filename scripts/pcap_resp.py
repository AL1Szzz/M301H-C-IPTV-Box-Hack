#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 pcap 提取 HTTP 响应体（按请求 URL 关键字过滤）"""
import struct, sys, re, os

path = sys.argv[1]
outdir = sys.argv[2] if len(sys.argv) > 2 else 'resp'
os.makedirs(outdir, exist_ok=True)
kw = sys.argv[3] if len(sys.argv) > 3 else None

d = open(path, 'rb').read()
endi = '<' if d[:4] == b'\xd4\xc3\xb2\xa1' else '>'
network = struct.unpack(endi + 'I', d[20:24])[0]
off = 24
n = 0
saved = 0
while off + 16 <= len(d):
    ts, tus, incl, orig = struct.unpack(endi + 'IIII', d[off:off + 16])
    off += 16
    data = d[off:off + incl]
    off += incl
    if network == 113:
        if len(data) < 16: continue
        proto = struct.unpack('>H', data[14:16])[0]; ip = data[16:]
    elif network == 1:
        if len(data) < 14: continue
        proto = struct.unpack('>H', data[12:14])[0]; ip = data[14:]
    else:
        ip = data; proto = 0x0800
    if proto != 0x0800 or len(ip) < 20: continue
    ihl = (ip[0] & 0xf) * 4
    if ip[9] != 6: continue
    tcp = ip[ihl:]
    if len(tcp) < 20: continue
    sp, dp = struct.unpack('>HH', tcp[:4])
    doff = (tcp[12] >> 4) * 4
    p = tcp[doff:]
    if not p: continue
    # 响应：以 HTTP/ 开头
    if not p[:5] == b'HTTP/': continue
    try:
        t = p.decode('utf8', 'ignore')
    except Exception:
        continue
    if '\r\n\r\n' not in t: continue
    head, body = t.split('\r\n\r\n', 1)
    if not body: continue
    lines = head.split('\r\n')
    status = lines[0]
    ctype = ''
    for l in lines:
        if l.lower().startswith('content-type:'):
            ctype = l.split(':', 1)[1].strip()
    # 只留 json/xml/text
    if not any(x in ctype for x in ('json', 'xml', 'text')): continue
    n += 1
    if kw and kw not in body and kw not in head: continue
    fn = os.path.join(outdir, 'resp_%03d_%d.txt' % (n, dp))
    with open(fn, 'w', encoding='utf8') as f:
        f.write('%s\nCT:%s\n\n%s' % (status, ctype, body[:200000]))
    saved += 1
    print('SAVED', fn, len(body), 'bytes |', status[:40], '|', ctype)
print('总响应', n, '保存', saved)
