# -*- coding: utf-8 -*-
"""按键序列导航 + 每步 dump 摘要
用法: tv_nav2.py 22,22,23  (keyevent 码用逗号分隔)
"""
import sys, time, subprocess, xml.etree.ElementTree as ET
from adbX import shell

KEYS = [int(k) for k in sys.argv[1].split(',')]

def dump():
    shell('rm -f /data/local/tmp/nv.xml')
    shell('uiautomator dump /data/local/tmp/nv.xml >/dev/null 2>&1', timeout=40)
    o, _ = shell('cat /data/local/tmp/nv.xml')
    if not o.strip().startswith('<?xml'):
        return None
    return ET.fromstring(o.strip())

def summary():
    r = dump()
    if r is None:
        return 'dump失败', []
    o, _ = shell('dumpsys window windows | grep mCurrentFocus')
    act = o.split('/')[-1].split('}')[0] if '/' in o else '?'
    texts, sel = [], []
    for n in r.iter('node'):
        t = (n.get('text') or n.get('content-desc') or '').strip()
        if not t:
            continue
        if n.get('selected') == 'true':
            sel.append(t)
        if len(texts) < 30:
            texts.append(t)
    return act, (sel, texts)

act, (sel, texts) = summary()
print('[初始] %s | SEL=%s' % (act, sel))
print('   ', ' / '.join(texts[:14]))

for k in KEYS:
    shell('input keyevent %d' % k)
    time.sleep(3)
    act, (sel, texts) = summary()
    print('[key %d] %s | SEL=%s' % (k, act, sel))
    print('   ', ' / '.join(texts[:14]))
