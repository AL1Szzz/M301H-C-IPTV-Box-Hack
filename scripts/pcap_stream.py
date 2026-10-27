#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TCP 流重组：从 pcap 还原完整 HTTP 会话，找出含关键字的响应"""
import struct, sys, os, re
from collections import OrderedDict

path = sys.argv[1]
outdir = sys.argv[2] if len(sys.argv) > 2 else 'streams'
kw = sys.argv[3] if len(sys.argv) > 3 else 'PLTV'
os.makedirs(outdir, exist_ok=True)

d = open(path, 'rb').read()
endi = '<' if d[:4] == b'\xd4\xc3\xb2\xa1' else '>'
network = struct.unpack(endi + 'I', d[20:24])[0]
off = 24
flows = OrderedDict()
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
    src = '.'.join(str(b) for b in ip[12:16])
    dst = '.'.join(str(b) for b in ip[16:20])
    tcp = ip[ihl:]
    if len(tcp) < 20: continue
    sp, dp, seq = struct.unpack('>HHI', tcp[:8])
    doff = (tcp[12] >> 4) * 4
    p = tcp[doff:]
    if not p: continue
    key = (src, sp, dst, dp)
    if key not in flows:
        flows[key] = {}
    # 按 seq 去重存放
    if seq not in flows[key] or len(p) > len(flows[key][seq]):
        flows[key][seq] = p

print('流数量:', len(flows))
hits = 0
for (key, segs) in flows.items():
    buf = b''.join(segs[s] for s in sorted(segs))
    if kw.encode() not in buf: continue
    hits += 1
    src, sp, dst, dp = key
    fn = os.path.join(outdir, 'flow_%s_%d_to_%s_%d.txt' % (src.replace('.', '_'), sp, dst.replace('.', '_'), dp))
    try:
        txt = buf.decode('utf8', 'ignore')
    except Exception:
        txt = repr(buf[:5000])
    with open(fn, 'w', encoding='utf8') as f:
        f.write(txt)
    # 打印概要
    first = txt.split('\r\n')[0][:120]
    # 找关键字上下文
    idx = txt.find(kw)
    ctx = txt[max(0, idx - 200): idx + 300].replace('\r\n', ' | ')
    print('=' * 70)
    print('FILE:', fn, '|', len(buf), 'bytes')
    print('SRC :', src, sp, '->', dst, dp)
    print('FIRST:', first)
    print('CTX  :', ctx[:500])
print('命中流:', hits)
