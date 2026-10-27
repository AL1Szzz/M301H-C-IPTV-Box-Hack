# -*- coding: utf-8 -*-
r"""
查 FongMi 存的配置、重启它、再导航到直播页看频道
"""
import os
import re
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEV = '192.168.50.104:5555'
TMP = r'C:\Users\Administrator\Downloads\apktmp\ui'
PKG = 'com.fongmi.android.tv'


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

    print('--- 已存的配置 ---')
    pref = sh(['shell', 'su', '-c',
               'cat /data/data/%s/shared_prefs/*.xml 2>/dev/null | grep -o "api[^<]*"' % PKG])
    print(pref.strip()[:400] or '(没读到)')

    print('--- 重启 FongMi ---')
    sh(['shell', 'am', 'force-stop', PKG])
    time.sleep(2)
    sh(['shell', 'monkey', '-p', PKG, '-c', 'android.intent.category.LAUNCHER', '1'])
    time.sleep(12)
    x = dump('c1')
    print('启动后:', ' | '.join(texts_of(x)[:12]))

    print('--- 进直播 ---')
    sh(['shell', 'input', 'keyevent', '22'])
    time.sleep(1.5)
    for _ in range(3):
        sh(['shell', 'input', 'keyevent', '21'])
        time.sleep(1.5)
    sh(['shell', 'input', 'keyevent', '66'])
    time.sleep(12)
    x = dump('c2')
    ts = texts_of(x)
    print('直播页文本(%d): %s' % (len(ts), ' | '.join(ts[:40]) if ts else '(空)'))
    sel = re.findall(r'<node[^>]*text="([^"]*)"[^>]*selected="true"', x)
    print('选中:', sel[:5])
    return 0


if __name__ == '__main__':
    sys.exit(main())
