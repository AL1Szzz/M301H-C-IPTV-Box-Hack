#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AK50 root 阶段 2b（补完）：
- 用 echo 写 /system/etc/install-recovery.sh（该 shell 无 printf）
- 启动 daemonsu 并确认进程存在
- 安装 SuperSU.apk
- 验证 su 版本
用法: python step2b.py [IP]
"""
import os
import subprocess
import sys
import time

ADB = r"C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe"
BASE = r"C:\Users\Administrator\Downloads\AK50-Root精简\tools"
SSU_APK = os.path.join(BASE, "SuperSU-v2.82-SR5.apk")
D = (sys.argv[1] if len(sys.argv) > 1 else "192.168.50.104") + ":5555"


def sh(args, t=60):
    try:
        p = subprocess.run([ADB, "-s", D] + args, capture_output=True, timeout=t)
        return ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "ignore").strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def raw(args, t=60):
    try:
        p = subprocess.run([ADB] + args, capture_output=True, timeout=t)
        return ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8", "ignore").strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def main():
    print("=" * 66)
    raw(["connect", D]); time.sleep(2)
    sh(["root"]); time.sleep(5)
    raw(["connect", D]); time.sleep(2)
    print("身份:", sh(["shell", "id"]))
    sh(["remount"]); sh(["shell", "mount -o rw,remount /system"])

    print("\n[1] 写 install-recovery.sh（用 echo）")
    sh(["shell", "echo '#!/system/bin/sh' > /system/etc/install-recovery.sh"])
    sh(["shell", "echo '/system/xbin/daemonsu --auto-daemon &' >> /system/etc/install-recovery.sh"])
    print("   chmod:", sh(["shell", "chmod 0755 /system/etc/install-recovery.sh"]) or "(ok)")
    print("   内容:\n   " + sh(["shell", "cat /system/etc/install-recovery.sh"]).replace("\n", "\n   "))

    print("\n[2] 启动 daemonsu 并验证")
    sh(["shell", "nohup /system/xbin/daemonsu --auto-daemon >/dev/null 2>&1 &"], 20)
    time.sleep(4)
    ps = sh(["shell", "ps"])
    hits = []
    for l in ps.splitlines():
        if "daemonsu" in l:
            hits.append(l.strip())
    print("   daemonsu 进程:", hits if hits else "(未运行)")
    print("   /system/xbin 下:", sh(["shell", "ls -l /system/xbin/su /system/xbin/daemonsu /system/xbin/su.bak"]).replace("\n", "\n      "))

    print("\n[3] su 版本")
    print("   ", sh(["shell", "/system/xbin/su -V"], 25))

    print("\n[4] 安装 SuperSU.apk")
    print("   ", raw(["-s", D, "install", "-r", SSU_APK], 240))
    print("   已装:", sh(["shell", "pm list packages | grep -i supersu"]))

    print("\n[5] 写入 /system/app 让 SuperSU 成为系统 app（可选，防被清理）")
    print("   ", sh(["shell", "ls /data/app/eu.chainfire.supersu* 2>&1"]))

    print("\n" + "=" * 66)
    print("完成。请重启电视，然后打开 SuperSU app，看是否显示 su 版本（不再是 'su binary 需要更新'）。")
    print("=" * 66)


if __name__ == "__main__":
    main()
