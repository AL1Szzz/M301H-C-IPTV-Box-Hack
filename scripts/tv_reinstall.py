# -*- coding: utf-8 -*-
r"""
把直播软件重装到【内部存储】（pm install -f），让它们不再依赖 U 盘

背景：这些 APK 默认被装到"外置存储"（这台电视 = U 盘），U 盘一拔系统就把它们
当成已卸载，第三方应用会集体消失。用 -f 强制装到内部存储即可。

用法：
    python tv_reinstall.py            # 装默认清单
    python tv_reinstall.py <包名>     # 只装指定
"""
import os
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEV = '192.168.50.104:5555'
APK_DIR = r'F:\AK50\04_APK'
REMOTE = '/data/local/tmp/tvinst.apk'

# 优先装这几个：my-tv(内置源) DIY直播 小微直播 ipv6 DIY2020 狐妖
DEFAULT = [
    'com.lizongying.mytv',
    'com.zhibotv.diyp.live',
    'com.live.zd',
    'com.player.ipv6',
    'com.player.dong.diyp2020',
    'com.player.wuyunyy',
]


def sh(a, t=180):
    try:
        r = subprocess.run([ADB, '-s', DEV] + a, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore').strip()
    except Exception as e:
        return 'TIMEOUT:%s' % e


def main():
    subprocess.run([ADB, 'connect', '192.168.50.104:5555'], capture_output=True, timeout=60)
    want = sys.argv[1:] or DEFAULT
    for pkg in want:
        src = os.path.join(APK_DIR, pkg + '.apk')
        if not os.path.exists(src):
            print('%-28s 缺 APK: %s' % (pkg, src))
            continue
        sh(['shell', 'rm', '-f', REMOTE])
        r = subprocess.run([ADB, '-s', DEV, 'push', src, REMOTE], capture_output=True, timeout=300)
        if 'pushed' not in (r.stdout + r.stderr).decode('utf-8', 'ignore'):
            print('%-28s push 失败' % pkg)
            continue
        out = sh(['shell', 'su', '-c', 'pm install -f -r %s' % REMOTE], 300)
        ok = 'Success' in out
        print('%-28s %s %s' % (pkg, 'OK' if ok else '失败', '' if ok else out[:80]))
        if ok:
            # 确认安装位置是内部
            path = sh(['shell', 'pm', 'path', pkg])
            print('      路径: %s' % path)
    sh(['shell', 'rm', '-f', REMOTE])
    print('\n剩余第三方:', sh(['shell', 'pm list packages -3']).count('package:'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
