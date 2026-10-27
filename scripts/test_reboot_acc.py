# -*- coding: utf-8 -*-
"""重启盒子 -> 等待 -> 检查服务绑定 + 测 MENU"""
import subprocess, time
ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.52:5555"
def run(*args, t=90):
    try:
        r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
        return ((r.stdout or '') + (r.stderr or '')).strip()
    except Exception as e:
        return 'TIMEOUT ' + str(e)
# 确保启用字符串已写好
print(run("connect", IP)); time.sleep(4)
print('acc set:', run("shell", "settings get secure enabled_accessibility_services"))
run("shell", "settings put secure accessibility_enabled 1")
run("shell", "reboot")
print('rebooting...')
time.sleep(100)
for i in range(6):
    print('try', i, run("connect", IP))
    time.sleep(8)
    if 'connected' in run("devices"):
        break
time.sleep(5)
print('== acc after boot ==')
print(run("shell", "dumpsys accessibility | busybox grep -i services | busybox head -2"))
print('== 进程 ==')
print(run("shell", "ps | busybox grep tv4"))
run("shell", "input keyevent 3"); time.sleep(6)
run("shell", "input keyevent 82"); time.sleep(7)
print('after MENU:', run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -1"))
print(run("shell", "logcat -d -s MenuKeySvc 2>&1 | busybox tail -8"))
