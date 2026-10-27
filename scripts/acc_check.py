# -*- coding: utf-8 -*-
import subprocess, time
ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.52:5555"
def run(*args, t=60):
    try:
        r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
        return ((r.stdout or '') + (r.stderr or '')).strip()
    except Exception as e:
        return 'TIMEOUT ' + str(e)
print(run("connect", IP)); time.sleep(4)
print('== dumpsys accessibility ==')
print(run("shell", "dumpsys accessibility | busybox head -30"))
