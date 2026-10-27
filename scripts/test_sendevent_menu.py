# -*- coding: utf-8 -*-
"""sendevent 注入菜单键(Linux scan code 139) 测无障碍按键过滤"""
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
# 先回 gitv 桌面
run("shell", "input keyevent 3"); time.sleep(6)
print('before:', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
run("shell", "logcat -c")
# sendevent: KEY_MENU=139
run("shell", "sendevent /dev/input/event0 1 139 1; sendevent /dev/input/event0 0 0 0; sendevent /dev/input/event0 1 139 0; sendevent /dev/input/event0 0 0 0")
time.sleep(7)
print('after :', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
print('log   :', run("shell", "logcat -d -s MenuKeySvc | busybox tail -6"))
