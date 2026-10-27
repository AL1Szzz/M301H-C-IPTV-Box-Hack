# -*- coding: utf-8 -*-
"""重装桌面 -> 重新启用无障碍 -> 测 MENU 切换"""
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
# 覆盖安装后服务可能掉了，重写开关
run("shell", "settings put secure enabled_accessibility_services app.orchard.tv4/.MenuKeyService")
run("shell", "settings put secure accessibility_enabled 1")
time.sleep(3)
print('acc:', run("shell", "dumpsys accessibility | busybox grep -A1 services | busybox head -3"))
# 测 MENU
run("shell", "input keyevent 3"); time.sleep(6)
run("shell", "input keyevent 82"); time.sleep(8)
print('after MENU:', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
