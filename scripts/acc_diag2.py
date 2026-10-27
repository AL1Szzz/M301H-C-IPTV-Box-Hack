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
print('== package 中的 service ==')
print(run("shell", "dumpsys package app.orchard.tv4 | busybox grep -B2 -A8 'Service' | busybox head -40"))
print('== 强制重绑: 重启 app 进程 ==')
run("shell", "am force-stop app.orchard.tv4")
time.sleep(2)
run("shell", "settings put secure enabled_accessibility_services ''")
time.sleep(2)
run("shell", "settings put secure enabled_accessibility_services app.orchard.tv4/.MenuKeyService")
time.sleep(5)
print('== 重绑后进程 ==')
print(run("shell", "ps | busybox grep tv4"))
run("shell", "input keyevent 82")
time.sleep(4)
print('== 日志 ==')
print(run("shell", "logcat -d -s MenuKeySvc 2>&1 | busybox tail -8"))
