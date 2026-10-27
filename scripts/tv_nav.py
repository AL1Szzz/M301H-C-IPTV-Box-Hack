# -*- coding: utf-8 -*-
r"""
FongMi 遥控器导航 + 抓界面文本（这台电视 screencap 不可用，只能靠 uiautomator）

用法：
    python tv_nav.py                 # 只 dump 当前界面
    python tv_nav.py 21 21 66        # 依次发按键（21=左 22=右 66=确定）后 dump
"""
import os
import re
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEV = '192.168.50.104:5555'
TMP = r'C:\Users\Administrator\Downloads\apktmp\ui'


def sh(a, t=90):
    try:
        r = subprocess.run([ADB, '-s', DEV] + a, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def dump(name):
    sh(['shell', 'uiautomator', 'dump', '/data/local/tmp/%s.xml' % name])
    local = os.path.join(TMP, name + '.xml')
    if os.path.exists(local):
        os.remove(local)
    subprocess.run([ADB, '-s', DEV, 'pull', '/data/local/tmp/%s.xml' % name, local],
                   capture_output=True, timeout=120)
    if not os.path.exists(local):
        return ''
    with open(local, encoding='utf-8', errors='ignore') as f:
        return f.read()


def texts_of(xml):
    return [t for t in re.findall(r'text="([^"]*)"', xml) if t.strip()]


def main():
    subprocess.run([ADB, 'connect', '192.168.50.104:5555'], capture_output=True, timeout=60)
    os.makedirs(TMP, exist_ok=True)
    keys = [a for a in sys.argv[1:] if a.isdigit()]
    for k in keys:
        sh(['shell', 'input', 'keyevent', k])
        time.sleep(1.2)
    time.sleep(8)
    xml = dump('nav')
    ts = texts_of(xml)
    print('界面文本(%d): %s' % (len(ts), ' | '.join(ts[:40]) if ts else '(无文本)'))
    sel = re.findall(r'<node[^>]*text="([^"]*)"[^>]*selected="true"', xml)
    sel += re.findall(r'<node[^>]*selected="true"[^>]*text="([^"]*)"', xml)
    print('当前选中:', sel[:5] if sel else '(无)')
    foc = re.findall(r'<node[^>]*focused="true"[^>]*text="([^"]*)"', xml)
    if foc:
        print('焦点:', foc[:5])
    ch = [t for t in ts if re.search(r'CCTV|卫视|央视|湖南|浙江|江苏|东方|北京|广东|山东|凤凰', t)]
    if ch:
        print('频道样例:', '、'.join(ch[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
