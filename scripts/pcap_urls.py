#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""解析 tcpdump -i any 抓的 pcap（LINUX_SLL），提取 HTTP 请求与流媒体地址"""
import struct, sys, re
from collections import Counter

def parse(path):
    d = open(path, 'rb').read()
    magic = d[:4]
    if magic == b'\xd4\xc3\xb2\xa1':
        endi = '<'
    elif magic == b'\xa1\xb2\xc3\xd4':
        endi = '>'
    else:
        print('unknown magic', magic); return []
    network = struct.unpack(endi + 'I', d[20:24])[0]
    LINK = {113: 'LINUX_SLL', 1: 'EN10MB', 0: 'NULL'}
    print('linktype =', network, LINK.get(network, '?'))
    off = 24
    pkts = []
    n = 0
    while off + 16 <= len(d):
        ts, tus, incl, orig = struct.unpack(endi + 'IIII', d[off:off + 16])
        off += 16
        data = d[off:off + incl]
        off += incl
        n += 1
        if network == 113:
            if len(data) < 16: continue
            proto = struct.unpack('>H', data[14:16])[0]
            ip = data[16:]
        elif network == 1:
            if len(data) < 14: continue
            proto = struct.unpack('>H', data[12:14])[0]
            ip = data[14:]
        else:
            ip = data
            proto = 0x0800
        if proto != 0x0800: continue
        if len(ip) < 20: continue
        ihl = (ip[0] & 0xf) * 4
        if ip[9] != 6: continue  # TCP only
        src = '.'.join(str(b) for b in ip[12:16])
        dst = '.'.join(str(b) for b in ip[16:20])
        tcp = ip[ihl:]
        if len(tcp) < 20: continue
        sp, dp = struct.unpack('>HH', tcp[:4])
        doff = (tcp[12] >> 4) * 4
        payload = tcp[doff:]
        if payload:
            pkts.append((src, sp, dst, dp, payload))
    print('parsed packets with payload:', len(pkts), '/', n)
    return pkts

def main(path):
    pkts = parse(path)
    http = []
    for (s, sp, d, dp, p) in pkts:
        if dp in (80, 8080, 443, 33200, 554) or sp in (80, 8080, 33200, 554):
            head = p[:900]
            if head[:3] in (b'GET', b'POS', b'PUT', b'HEA') or head[:4] == b'HTTP':
                try:
                    t = head.decode('utf8', 'ignore')
                except Exception:
                    continue
                http.append((s, sp, d, dp, t))
    print('=== HTTP 报文数:', len(http), '===')
    urls = []
    for (s, sp, d, dp, t) in http:
        first = t.split('\r\n')[0]
        hostm = re.search(r'Host:\s*([^\r\n]+)', t)
        host = hostm.group(1).strip() if hostm else ''
        if first.startswith(('GET', 'POST')):
            m = re.match(r'(GET|POST)\s+(\S+)\s+HTTP', first)
            if m:
                url = 'http://' + (host or d) + m.group(2)
                urls.append(url)
    uniq = []
    seen = set()
    for u in urls:
        key = re.sub(r'[?&](gTimestamp|gRequests|_|t|r)=\d+', '', u)
        if key in seen: continue
        seen.add(key)
        uniq.append(u)
    print('=== 唯一 URL:', len(uniq), '===')
    # 只看流媒体 / EPG / 认证相关
    KW = ['223.110', '223.111', 'gitv', 'EPG', 'live', 'Live', 'LIVE', 'm3u8', 'ts?', 'rtsp',
          'auth', 'Auth', 'play', 'Play', 'channel', 'Channel', 'playbill', 'playurl', 'PlayUrl']
    print('\n########## 关键 URL（流媒体/EPG/认证）##########')
    for u in uniq:
        if any(k in u for k in KW):
            print(u[:400])
    print('\n########## 全部 URL 前 120 条 ##########')
    for u in uniq[:120]:
        print(u[:250])

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'cap.pcap')
