# -*- coding: utf-8 -*-
"""重装 + 清 logcat + 按 MENU + 抓日志"""
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
print(run("push", r"F:/AK50/04_APK/AerialTV4.apk", "/data/local/tmp/tv4.apk", t=120))
print(run("shell", "pm install -f -r /data/local/tmp/tv4.apk"))
run("shell", "settings put secure enabled_accessibility_services ''")
time.sleep(2)
run("shell", "settings put secure enabled_accessibility_services app.orchard.tv4/.MenuKeyService")
run("shell", "settings put secure accessibility_enabled 1")
time.sleep(3)
run("shell", "logcat -c")
run("shell", "input keyevent 3"); time.sleep(5)
run("shell", "input keyevent 82"); time.sleep(6)
print('== logcat MenuKeySvc ==')
print(run("shell", "logcat -d -s MenuKeySvc 2>&1 | busybox tail -12"))
print('fg:', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
