# -*- coding: utf-8 -*-
import os, codecs
from rc_client import get, cmd
OUT = r"F:/AK50/06_系统快照/盒子"
os.makedirs(OUT, exist_ok=True)
CMDS = [
 ("id",           "id; echo ---; ls -l /init.rc; echo ---; head -c 200 /init.rc 2>&1"),
 ("pkgs",         "pm list packages -f 2>&1"),
 ("ps",           "ps 2>&1"),
 ("bin",          "ls -l /system/bin 2>&1"),
 ("xbin",         "ls -l /system/xbin 2>&1"),
 ("app",          "ls -l /system/app 2>&1"),
 ("etc",          "ls -l /system/etc 2>&1"),
 ("tmp",          "ls -l /data/local/tmp 2>&1"),
 ("root",         "ls -l / 2>&1"),
 ("prop_adb",     "getprop | grep -iE 'adb|usb|debug|secure' 2>&1"),
 ("build",        "getprop | grep -iE 'build|version' 2>&1"),
 ("suinfo",       "ls -l /system/xbin/su /system/bin/su 2>&1; ls -l /system/app/Super* 2>&1; ls -l /data/system 2>&1"),
]
for name, c in CMDS:
    r = cmd(c)
    p = os.path.join(OUT, "box_%s.txt" % name)
    codecs.open(p, "w", "utf-8").write(r)
    print("%-10s %6dB -> %s" % (name, len(r), p))
for ep, fn in (("/props","box_props.txt"), ("/log","box_log.txt"), ("/mounts","box_mounts.txt"), ("/pkg","box_pkg3.txt")):
    r = get(ep)
    p = os.path.join(OUT, fn)
    codecs.open(p, "w", "utf-8").write(r)
    print("%-10s %6dB -> %s" % (ep, len(r), fn))
