#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AK50 root 阶段 1：连接 -> 提权 -> 探测 /system 可写性 -> 探测 su 行为
用法: python step1.py [IP]
"""
import subprocess
import sys
import time

ADB = r"C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe"
D = (sys.argv[1] if len(sys.argv) > 1 else "192.168.50.104") + ":5555"


def sh(args, t=40):
    try:
        p = subprocess.run([ADB, "-s", D] + args, capture_output=True, timeout=t)
        return ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "ignore").strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def raw(args, t=40):
    try:
        p = subprocess.run([ADB] + args, capture_output=True, timeout=t)
        return ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "ignore").strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def main():
    print("=" * 66)
    print("设备: %s" % D)
    print("=" * 66)
    print("[1] connect :", raw(["connect", D]))
    time.sleep(2)
    print("[2] root    :", sh(["root"]))
    time.sleep(5)
    print("[3] connect :", raw(["connect", D]))
    time.sleep(2)
    print("[4] devices :", raw(["devices", "-l"]).splitlines()[-1] if raw(["devices", "-l"]) else "?")

    print("\n[5] 身份    :", sh(["shell", "id"]))

    print("\n[6] remount rw 尝试")
    print("   mount -o rw,remount :", sh(["shell", "mount -o rw,remount /system"]) or "(无输出=成功)")
    print("   adb remount         :", sh(["remount"]))
    m = sh(["shell", "mount"])
    for l in m.splitlines():
        if " /system " in l:
            print("   /system 现状:", l.strip())

    print("\n[7] 写测试")
    print("  ", sh(["shell", "touch /system/.rwtest && echo WRITE_OK || echo WRITE_FAIL"]))
    print("  ", sh(["shell", "ls -l /system/.rwtest 2>&1 | head -1"]))
    sh(["shell", "rm -f /system/.rwtest"])

    print("\n[8] su 行为探测")
    print("   su -V          :", sh(["shell", "/system/xbin/su -V 2>&1 | head -2"]))
    print("   su 10000 id    :", sh(["shell", "su 10000 id 2>&1 | head -3"]))
    print("   su 2000 id     :", sh(["shell", "su 2000 id 2>&1 | head -3"]))

    print("\n[9] 已有 superuser 管理 app?")
    apps = sh(["shell", "pm list packages | grep -iE 'super|chainfire|king|root'"])
    print("  ", apps or "(无)")

    print("\n[10] /system/xbin 内容")
    print("  ", sh(["shell", "ls -l /system/xbin/ 2>&1 | head -12"]).replace("\n", "\n   "))

    print("\n[11] install-recovery.sh / daemonsu 是否存在")
    print("  ", sh(["shell", "ls -l /system/etc/install-recovery.sh /system/bin/daemonsu /system/xbin/daemonsu 2>&1 | head -5"]))

    print("\n" + "=" * 66)
    print("完成")


if __name__ == "__main__":
    main()
