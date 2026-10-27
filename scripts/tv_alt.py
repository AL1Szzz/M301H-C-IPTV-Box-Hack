# -*- coding: utf-8 -*-
r"""
不依赖 /sdcard 的备选验证：启动内置源的直播软件（my-tv / DIY直播），看有没有真在播
用法：python tv_alt.py [包名]
"""
import os
import re
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEV = '192.168.50.104:5555'
TMP = r'C:\Users\Administrator\Downloads\apktmp\ui'

CAND = [
    ('com.lizongying.mytv', 'my-tv（内置源）'),
    ('com.zhibotv.diyp.live', 'DIY直播（内置源）'),
    ('com.live.zd', '小微直播'),
]


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
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for pkg, desc in CAND:
        if only and pkg != only:
            continue
        # 先把 FongMi 踢下去，否则它一直占着前台，测的全是它的界面
        sh(['shell', 'am', 'force-stop', 'com.fongmi.android.tv'])
        sh(['shell', 'input', 'keyevent', '3'])
        time.sleep(2)
        sh(['shell', 'logcat', '-c'])
        sh(['shell', 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1'])
        time.sleep(20)
        x = dump('alt_' + pkg.split('.')[-1])
        ts = texts_of(x)
        log = sh(['shell', 'logcat', '-d'])
        play = [l.strip()[:90] for l in log.splitlines()
                if any(k in l for k in ('ExoPlayer', 'IJKMEDIA', 'VideoView', 'MediaPlayer',
                                        'openVideo', 'setDataSource', 'onPrepared'))][:2]
        ch = [t for t in ts if re.search(r'CCTV|卫视|央视|湖南|浙江|江苏|东方|北京|广东', t)]
        print('\n%-22s %s' % (pkg, desc))
        print('  界面文本(%d): %s' % (len(ts), ' | '.join(ts[:15]) if ts else '(无文本=可能全屏播放)'))
        print('  频道关键字: %s' % (ch[:6] if ch else '无'))
        for p in play:
            print('  播放日志: %s' % p)
        sh(['shell', 'am', 'force-stop', pkg])
    return 0


if __name__ == '__main__':
    sys.exit(main())
