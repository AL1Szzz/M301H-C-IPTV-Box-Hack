# -*- coding: utf-8 -*-
"""一次性: 连电视(.17) -> 推送 -> 安装 -> 重启 AK 直播"""
import subprocess, time

ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.17:5555"

def run(*args, t=90):
    r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
    return ((r.stdout or '') + (r.stderr or '')).strip()

print(run("connect", IP)); time.sleep(4)
print(run("push", r"F:/AK50/04_APK/AKLiveTV.apk", "/data/local/tmp/tv.apk", t=120))
print(run("shell", "su -c 'pm install -f -r /data/local/tmp/tv.apk'"))
print(run("shell", "su -c 'am force-stop app.orchard.livetv'"))
time.sleep(1)
print(run("shell", "monkey -p app.orchard.livetv -c android.intent.category.LAUNCHER 1"))
time.sleep(8)
# 验证: 前台 + 视频帧推进
print(run("shell", "dumpsys activity activities | busybox grep -i mFocusedActivity | busybox head -2"))
print('vo_frames:', run("shell", "logcat -d | busybox grep -c '\\[vo\\]'"))
