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
# 清 AerialTV4 残留对话框: 回 HOME -> 进 AerialTV4 -> BACK -> HOME
run("shell", "input keyevent 4"); time.sleep(2)
run("shell", "input keyevent 3"); time.sleep(4)
print('done, fg:', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
