# -*- coding: utf-8 -*-
"""电视信息体检：系统应用、冻结列表、包版本与入口"""
import re
from adbX import shell

print('=== /system/app ===')
o, _ = shell('ls /system/app/')
print(o.strip())

print('\n=== 冻结(Disabled) ===')
o, _ = shell('pm list packages -d')
frozen = [l.split(':')[-1].strip() for l in o.splitlines() if l.startswith('package:')]
print(len(frozen), '个:', ' '.join(frozen))

print('\n=== 第三方包 ===')
o, _ = shell('pm list packages -3')
third = [l.split(':')[-1].strip() for l in o.splitlines() if l.startswith('package:')]
print(' '.join(third))

for pkg in ['com.miaokantv.live', 'com.fongmi.android.tv', 'com.dangbei.lerad.videoposter',
            'com.konka.tvmall', 'com.dangbeimarket']:
    print('\n=== %s ===' % pkg)
    o, _ = shell('dumpsys package %s' % pkg, timeout=40)
    ver = re.search(r'versionName=([^\s]+)', o)
    code = re.search(r'versionCode=(\d+)', o)
    print('version:', ver.group(1) if ver else '-', 'code:', code.group(1) if code else '-')
    acts = re.findall(r'^\s*([0-9a-f]{8}) ([^\s]+)/([^\s]+) filter', o, re.M)
    launcher = re.findall(r'([^\s]+/[^\s]+) filter [0-9a-f]{8}\s*$', o, re.M)
    # 主 Activity（有 MAIN+LAUNCHER 的）
    blocks = o.split('Activity Resolver Table:')
    names = set()
    for b in o.split('\n'):
        m = re.match(r'\s*([0-9a-f]{8}) (\S+/\S+) filter', b)
        if m:
            names.add(m.group(2))
    print('activities:', len(names))
    for n in sorted(names)[:12]:
        print('  ', n)
