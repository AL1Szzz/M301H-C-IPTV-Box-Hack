# -*- coding: utf-8 -*-
"""清理设备（盒子 / 电视）上的调试残留：临时 APK、截图、抓包。

用法:
  python cleanup_devices.py            # 清理所有已配置的设备
  python cleanup_devices.py 192.168.50.52   # 只清理盒子

设备离线时会跳过并提示（需先唤醒设备 / 重启让 adbd 起来）。
"""
import subprocess
import sys

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEVICES = ['192.168.50.52', '192.168.50.17']   # 盒子 / 电视

CLEAN = ('rm -f /data/local/tmp/*.apk /mnt/sdcard/*.png /mnt/sdcard/*.pcap '
         '/mnt/sdcard/*.bin 2>/dev/null; echo done')


def sh(args, timeout=60):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return ((p.stdout or '') + (p.stderr or '')).strip()


def main():
    targets = sys.argv[1:] or DEVICES
    for ip in targets:
        print('=== %s ===' % ip)
        out = sh([ADB, 'connect', ip + ':5555'])
        if 'connected to' not in out:
            print('  离线，跳过（%s）' % out.splitlines()[0] if out else '  离线，跳过')
            continue
        print(' ', sh([ADB, '-s', ip + ':5555', 'shell', CLEAN]))
        left = sh([ADB, '-s', ip + ':5555',
                   'shell', 'ls /data/local/tmp/ /mnt/sdcard/ 2>/dev/null | grep -cE "apk|png|pcap"'])
        print('  残留计数:', left)
    print('\n如需断开:', '"%s" kill-server' % ADB)


if __name__ == '__main__':
    main()
