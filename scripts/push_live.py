# -*- coding: utf-8 -*-
"""把直播源推到电视 /sdcard（现在已可写）"""
import os
from adbX import run

SRC = r'F:\AK50\05_直播源'
files = ['live.m3u', 'ipv6_only.m3u', 'config.json']

for f in files:
    local = os.path.join(SRC, f)
    if not os.path.exists(local):
        print('缺文件', f)
        continue
    out, err = run(['push', local, '/sdcard/' + f], timeout=60)
    print(f, '->', (out or err).strip()[:120])

out, _ = run(['shell', 'ls -la /sdcard/'], timeout=30)
print('\n=== /sdcard 内容 ===')
print(out.strip())
