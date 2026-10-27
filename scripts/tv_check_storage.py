# -*- coding: utf-8 -*-
r"""
改完 mstar.usb.as.sdcard=false 后验证内置存储是否顶上来
"""
import os
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEV = '192.168.50.104:5555'


def sh(a, t=90):
    try:
        r = subprocess.run([ADB, '-s', DEV] + a, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore').strip()
    except Exception as e:
        return 'TIMEOUT'


def main():
    for i in range(20):
        subprocess.run([ADB, 'connect', '192.168.50.104:5555'], capture_output=True, timeout=60)
        d = subprocess.run([ADB, 'devices'], capture_output=True, timeout=30).stdout.decode()
        st = [l for l in d.splitlines() if '192.168' in l]
        if st and 'device' in st[0] and 'offline' not in st[0]:
            print('第%d次连上' % i)
            break
        time.sleep(8)
    else:
        print('等不到电视')
        return 1

    time.sleep(3)
    print('属性 usb.as.sdcard =', sh(['shell', 'getprop mstar.usb.as.sdcard']))
    print('EXTERNAL_STORAGE =', sh(['shell', 'getprop']).count('EXTERNAL_STORAGE') and '有' or '无')
    print('--- 挂载 ---')
    for l in sh(['shell', 'su -c cat /proc/mounts']).splitlines():
        if 'fuse' in l or 'media_rw' in l:
            print(' ', l)
    print('--- /sdcard ---')
    print('文件数:', sh(['shell', 'ls /sdcard/ 2>&1 | busybox wc -l']))
    print('列表:', sh(['shell', 'ls /sdcard/ 2>&1'])[:300])
    print('root写测试:', sh(['shell', 'su -c "echo hi > /sdcard/_w.txt 2>&1; ls -l /sdcard/_w.txt 2>&1"']))
    print('data/media/0:', sh(['shell', 'su -c "ls -la /data/media/0/ 2>&1"'])[:300])
    return 0


if __name__ == '__main__':
    sys.exit(main())
