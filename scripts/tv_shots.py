# -*- coding: utf-8 -*-
r"""
对已装的 TV 应用逐个启动并截图，用来判断到底能不能看（有没有台 / 报不报错）

用法：python tv_shots.py
输出：shots2\NN_pkg.png
"""
import json
import os
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
HOST = '192.168.50.104'
DEV = HOST + ':5555'
OUT = r'C:\Users\Administrator\Downloads\AK50-Root精简\shots2'
REPORT = r'C:\Users\Administrator\Downloads\AK50-Root精简\tv2_report.json'


def adb(args, t=120):
    try:
        r = subprocess.run([ADB, '-s', DEV] + args, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def main():
    subprocess.run([ADB, 'connect', HOST], capture_output=True, timeout=60)
    time.sleep(2)
    os.makedirs(OUT, exist_ok=True)
    man = json.load(open(REPORT, encoding='utf-8'))
    todo = [m for m in man if m.get('alive')]
    only = sys.argv[1:] or None
    if only:
        todo = [m for m in todo if m['pkg'] in only]

    for n, m in enumerate(todo, 1):
        pkg = m['pkg']
        adb(['shell', 'logcat', '-c'])
        adb(['shell', 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1'], 60)
        time.sleep(14)
        name = '%02d_%s.png' % (n, pkg)
        adb(['shell', 'screencap', '-p', '/sdcard/shot.png'], 60)
        adb(['pull', '/sdcard/shot.png', os.path.join(OUT, name)], 120)
        log = adb(['shell', 'logcat', '-d'])
        hits = [l.strip()[:110] for l in log.splitlines()
                if any(k in l for k in ('播放', '直播源', 'Error', 'error', 'Exception',
                                        'timeout', 'failed', '无法', '失败', 'null'))
                and pkg in l][:3]
        m['shot'] = name
        m['loghits'] = hits
        print('%-28s -> %s' % (pkg, name))
        for h in hits:
            print('      %s' % h)
        adb(['shell', 'am', 'force-stop', pkg])

    json.dump(man, open(REPORT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('\n截图目录：%s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
