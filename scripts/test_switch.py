# -*- coding: utf-8 -*-
"""验证: HOME -> gitv 桌面; MENU -> AerialTV4"""
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
# 1. 先回 HOME
run("shell", "input keyevent 3"); time.sleep(8)
print('after HOME :', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
# 2. 按 MENU
run("shell", "input keyevent 82"); time.sleep(8)
print('after MENU :', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
run("shell", "screencap -p /mnt/sdcard/m1.png")
print(run("pull", "/mnt/sdcard/m1.png", r"F:/AK50/boxbak/m1.png", t=60))
# 3. 再按 HOME 应回 gitv
run("shell", "input keyevent 3"); time.sleep(8)
print('HOME again :', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
run("shell", "screencap -p /mnt/sdcard/m2.png")
print(run("pull", "/mnt/sdcard/m2.png", r"F:/AK50/boxbak/m2.png", t=60))
