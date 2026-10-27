# -*- coding: utf-8 -*-
"""稳定的 adb 调用封装：带 daemon 保活 + 自动重连 + 重试"""
import subprocess, time, sys, os

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
HOST = '192.168.50.104:5555'


def run(args, timeout=30, retry=3):
    for i in range(retry):
        try:
            p = subprocess.run([ADB] + args, capture_output=True, timeout=timeout)
            out = p.stdout.decode('utf-8', 'replace')
            err = p.stderr.decode('utf-8', 'replace')
            if 'no devices/emulators found' in err or 'device offline' in err or 'device not found' in err:
                subprocess.run([ADB, 'kill-server'], capture_output=True, timeout=15)
                time.sleep(1)
                subprocess.run([ADB, 'start-server'], capture_output=True, timeout=20)
                time.sleep(1)
                subprocess.run([ADB, 'connect', HOST], capture_output=True, timeout=20)
                time.sleep(2)
                continue
            return out, err
        except subprocess.TimeoutExpired:
            if i == retry - 1:
                return '', 'TIMEOUT'
            time.sleep(1)
    return '', 'GIVE_UP'


def shell(cmd, timeout=40, su=False):
    if su:
        cmd = 'su -c "%s"' % cmd.replace('"', '\\"')
    return run(['shell', cmd], timeout=timeout)


if __name__ == '__main__':
    cmd = sys.argv[1]
    su = '--su' in sys.argv
    if su:
        cmd = ' '.join(a for a in sys.argv[1:] if a != '--su')
    o, e = shell(cmd, su=su)
    sys.stdout.write(o)
    if e.strip():
        sys.stdout.write('\n[ERR] ' + e)
