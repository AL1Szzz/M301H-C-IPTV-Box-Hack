# -*- coding: utf-8 -*-
# 一次性完成: connect -> cp -> pull
import subprocess, time, sys

ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.52:5555"

def run(*args, t=30):
    r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
    return (r.stdout + r.stderr).strip()

print(run("connect", IP))
time.sleep(4)
print(run("devices"))
print(run("shell", "cp /data/data/com.gitv.tv.live/shared_prefs/EPG_CACHE_DATA.xml /data/local/epg.xml; chmod 644 /data/local/epg.xml; ls -la /data/local/epg.xml"))
print(run("pull", "/data/local/epg.xml", "F:/AK50/06_系统快照/盒子/cap/EPG_CACHE_DATA.xml"))
