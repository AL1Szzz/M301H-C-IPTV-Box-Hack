# -*- coding: utf-8 -*-
import subprocess, time
ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.52:5555"
def run(*args, t=90):
    try:
        r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
        return ((r.stdout or '') + (r.stderr or '')).strip()
    except Exception as e:
        return 'TIMEOUT ' + str(e)
print(run("connect", IP)); time.sleep(4)
print('== tv4 进程 ==')
print(run("shell", "ps | busybox grep tv4"))
print('== AMS 日志 ==')
print(run("shell", "logcat -d | busybox grep -iE 'accessibility|MenuKey|tv4' | busybox tail -20"))
