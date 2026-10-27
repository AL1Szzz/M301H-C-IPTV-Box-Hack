#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AK50 root 阶段 2：把 AOSP su 换成 SuperSU su（app 可申请 root）
- 备份原厂 su -> /system/xbin/su.bak
- 安装 armv7/su -> /system/xbin/su        (0755)
- 复制          -> /system/xbin/daemonsu  (0755)
- 写 /system/etc/install-recovery.sh（开机自动拉起 daemonsu）
- 立即启动 daemonsu
- 安装 SuperSU.apk
用法: python step2_install_root.py [IP]
"""
import os
import subprocess
import sys
import time

ADB = r"C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe"
BASE = r"C:\Users\Administrator\Downloads\AK50-Root精简\tools"
SU_ARMV7 = os.path.join(BASE, "su_supersu_armv7")
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
    for f, n in [(SU_ARMV7, "SuperSU su(armv7)"), (SSU_APK, "SuperSU.apk")]:
        if not os.path.exists(f):
            print("!! 缺少文件: %s (%s)" % (n, f))
            return

    print("=" * 66)
    print("目标:", D)
    print("=" * 66)
    raw(["connect", D]); time.sleep(2)
    sh(["root"]); time.sleep(5)
    raw(["connect", D]); time.sleep(2)
    print("身份:", sh(["shell", "id"]))

    print("\n[1] remount /system rw")
    print("   ", sh(["remount"]) or "(ok)")
    print("   ", sh(["shell", "mount -o rw,remount /system"]) or "(ok)")

    print("\n[2] 备份原厂 su")
    print("   ", sh(["shell", "cp /system/xbin/su /system/xbin/su.bak && echo BACKUP_OK || echo BACKUP_FAIL"]))
    print("   ", sh(["shell", "ls -l /system/xbin/su.bak"]))

    print("\n[3] push SuperSU su -> /system/xbin/su")
    print("   ", raw(["-s", D, "push", SU_ARMV7, "/system/xbin/su"], 120))
    print("   chmod:", sh(["shell", "chmod 0755 /system/xbin/su"]) or "(ok)")
    print("   ", sh(["shell", "ls -l /system/xbin/su"]))

    print("\n[4] 建 daemonsu")
    print("   ", sh(["shell", "cp /system/xbin/su /system/xbin/daemonsu && chmod 0755 /system/xbin/daemonsu && echo DAEMONSU_OK || echo DAEMONSU_FAIL"]))

    print("\n[5] 写 /system/etc/install-recovery.sh（开机自启 daemonsu）")
    cmd = ("printf '#!/system/bin/sh\\n/system/xbin/daemonsu --auto-daemon &\\n' "
           "> /system/etc/install-recovery.sh && chmod 0755 /system/etc/install-recovery.sh "
           "&& echo INSTALL_RECOVERY_OK || echo INSTALL_RECOVERY_FAIL")
    print("   ", sh(["shell", cmd]))
    print("   ", sh(["shell", "cat /system/etc/install-recovery.sh"]))

    print("\n[6] 立即启动 daemonsu")
    print("   ", sh(["shell", "/system/xbin/daemonsu --auto-daemon &"], 20))
    time.sleep(3)
    ps = sh(["shell", "ps"])
    hits = [l.strip() for l in ps.splitlines() if "daemonsu" in l or "su" in l.split()[-1]]
    print("   相关进程:", hits if hits else "(未见，重启后再看)")

    print("\n[7] 安装 SuperSU.apk")
    print("   ", raw(["-s", D, "install", "-r", SSU_APK], 180))

    print("\n[8] 验证")
    print("   su 权限:", sh(["shell", "ls -l /system/xbin/su /system/xbin/daemonsu /system/xbin/su.bak"]))
    pkg = sh(["shell", "pm list packages | grep -i supersu"])
    print("   SuperSU 包:", pkg or "(未安装)")
    print("   su -V   :", sh(["shell", "/system/xbin/su -V"], 20))

    print("\n" + "=" * 66)
    print("完成。建议重启电视后打开 SuperSU app 验证。")
    print("回滚：cp /system/xbin/su.bak /system/xbin/su && rm /system/etc/install-recovery.sh")
    print("=" * 66)


if __name__ == "__main__":
    main()
