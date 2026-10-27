# -*- coding: utf-8 -*-
import subprocess, time

ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.52:5555"

def run(*args, t=30):
    r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
    return (r.stdout + r.stderr).strip()

print(run("connect", IP))
time.sleep(4)
print(run("shell", "ls -la /data/data/com.gitv.tv.live/shared_prefs/"))
print(run("shell", "grep -c chnCode /data/data/com.gitv.tv.live/shared_prefs/*.xml 2>/dev/null"))
