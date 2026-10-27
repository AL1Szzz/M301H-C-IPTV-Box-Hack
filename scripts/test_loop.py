# -*- coding: utf-8 -*-
"""完整闭环: gitv -> [MENU] -> AerialTV4 -> [HOME] -> gitv"""
import subprocess, time
ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.52:5555"
def run(*args, t=90):
    try:
        r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
        return ((r.stdout or '') + (r.stderr or '')).strip()
    except Exception as e:
        return 'TIMEOUT ' + str(e)
MENU = ("sendevent /dev/input/event0 1 139 1; sendevent /dev/input/event0 0 0 0; "
        "sendevent /dev/input/event0 1 139 0; sendevent /dev/input/event0 0 0 0")
print(run("connect", IP)); time.sleep(4)
run("shell", "input keyevent 3"); time.sleep(6)
print('1.HOME后   :', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
run("shell", MENU); time.sleep(8)
print('2.菜单键后 :', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
run("shell", "screencap -p /mnt/sdcard/c1.png")
run("pull", "/mnt/sdcard/c1.png", r"F:/AK50/boxbak/c1.png", t=60)
# AerialTV4 里按 HOME
run("shell", "input keyevent 3"); time.sleep(7)
print('3.再按HOME :', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
run("shell", "screencap -p /mnt/sdcard/c2.png")
run("pull", "/mnt/sdcard/c2.png", r"F:/AK50/boxbak/c2.png", t=60)
