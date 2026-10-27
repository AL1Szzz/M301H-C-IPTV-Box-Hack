#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 pcap 导出完整 HTTP URL（不截断）"""
import struct, sys, re

path = sys.argv[1] if len(sys.argv) > 1 else 'cap.pcap'
outfile = sys.argv[2] if len(sys.argv) > 2 else 'urls.txt'

d = open(path, 'rb').read()
magic = d[:4]
endi = '<' if magic == b'\xd4\xc3\xb2\xa1' else '>'
network = struct.unpack(endi + 'I', d[20:24])[0]
off = 24
res = []
while off + 16 <= len(d):
    ts, tus, incl, orig = struct.unpack(endi + 'IIII', d[off:off + 16])
    off += 16
    data = d[off:off + incl]
    off += incl
    if network == 113:
        if len(data) < 16: continue
        proto = struct.unpack('>H', data[14:16])[0]
        ip = data[16:]
    elif network == 1:
        if len(data) < 14: continue
        proto = struct.unpack('>H', data[12:14])[0]
        ip = data[14:]
    else:
        ip = data; proto = 0x0800
    if proto != 0x0800 or len(ip) < 20: continue
    ihl = (ip[0] & 0xf) * 4
    if ip[9] != 6: continue
    tcp = ip[ihl:]
    if len(tcp) < 20: continue
    doff = (tcp[12] >> 4) * 4
    p = tcp[doff:]
    if not p: continue
    if p[:3] not in (b'GET', b'POS', b'HEA'): continue
    try:
        t = p[:3000].decode('utf8', 'ignore')
    except Exception:
        continue
    first = t.split('\r\n')[0]
    m = re.match(r'(GET|POST|HEAD)\s+(\S+)\s+HTTP', first)
    hm = re.search(r'Host:\s*([^\r\n]+)', t)
    src = '.'.join(str(b) for b in ip[12:16])
    dst = '.'.join(str(b) for b in ip[16:20])
    if m:
        host = hm.group(1).strip() if hm else dst
        res.append((src, dst, 'http://' + host + m.group(2), t))
print('GET/POST 请求数:', len(res))
uniq = []
seen = set()
for (s, dt, u, t) in res:
    k = re.sub(r'\d{10}-\d+-\d+\.hls\.ts', 'TS', u)
    if k in seen: continue
    seen.add(k)
    uniq.append((s, dt, u, t))
print('去重后:', len(uniq))
with open(outfile, 'w', encoding='utf8') as f:
    for (s, dt, u, t) in uniq:
        f.write('### %s -> %s\n%s\n\n' % (s, dt, u))
print('已写入', outfile)
for (s, dt, u, t) in uniq:
    print('---', s, '->', dt, 'len=%d' % len(u))
    print(u)
