#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
康佳 AK50 刷机后 —— 连接体检 + 只读备份脚本（不做任何修改）

用法:
    python tv_probe.py 192.168.50.104

会做:
  1. adb connect IP:5555 -> adb root -> 重新连接
  2. 只读采集: 身份(uid) / 系统属性 / 分区挂载 / su 是否存在 / 完整包名清单 / 常驻进程 / 内存
  3. 全部保存到 out/ 目录, 并打印关键结论

安全: 全程只读, 不 disable、不 uninstall、不写 /system。
"""
import os
import re
import subprocess
import sys
import time

ADB = r"C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe"
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "out")

GETPROP_KEYS = [
    "ro.build.version.release", "ro.build.version.sdk", "ro.build.type",
    "ro.build.display.id", "ro.build.fingerprint",
    "ro.secure", "ro.debuggable", "ro.adb.secure",
    "ro.product.model", "ro.product.brand", "ro.product.device",
    "ro.board.platform", "konka.platform", "konka.version",
    "persist.adb.tcp.port", "service.adb.tcp.port",
    "ro.build.version.incremental", "sys.usb.config",
]


def sh(args, timeout=30):
    """执行 adb 命令, 返回 (returncode, stdout+stderr)"""
    try:
        p = subprocess.run(args, capture_output=True, timeout=timeout)
        out = (p.stdout or b"").decode("utf-8", "ignore") + (p.stderr or b"").decode("utf-8", "ignore")
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:  # noqa
        return -2, str(e)


def save(name, text):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)
    return path


def main():
    if len(sys.argv) < 2:
        print("用法: python tv_probe.py <电视IP>")
        return
    ip = sys.argv[1].strip()
    os.makedirs(OUT, exist_ok=True)
    dev = "%s:5555" % ip

    print("=" * 70)
    print("目标: %s" % dev)
    print("=" * 70)

    # 1. connect
    rc, out = sh([ADB, "connect", dev], timeout=30)
    print("[connect] %s" % out.strip())
    if "connected to" not in out and "already connected" not in out:
        print("\n!! 连接失败。检查: IP 是否正确 / 工厂菜单里的 ADB 是否已打开 / 电视和电脑是否同网段")
        return
    time.sleep(2)

    # 2. adb root
    rc, out = sh([ADB, "-s", dev, "root"], timeout=30)
    print("[adb root] %s" % out.strip())
    time.sleep(4)
    rc, out = sh([ADB, "connect", dev], timeout=30)
    print("[reconnect] %s" % out.strip())
    time.sleep(2)

    # 3. 身份
    rc, who = sh([ADB, "-s", dev, "shell", "id"], timeout=20)
    who = who.strip()
    print("\n[身份] %s" % who)
    is_root = "uid=0" in who
    print("  -> %s" % ("★ 已经是 root (uid=0)" if is_root else "非 root，需要另行提权"))

    # 4. 系统属性
    lines = []
    for k in GETPROP_KEYS:
        rc, v = sh([ADB, "-s", dev, "shell", "getprop", k], timeout=15)
        lines.append("%s = %s" % (k, v.strip()))
    prop = "\n".join(lines)
    print("\n[系统属性]")
    for l in lines:
        print("  " + l)
    save("getprop.txt", prop)

    # 5. 分区挂载
    rc, mnt = sh([ADB, "-s", dev, "shell", "mount"], timeout=20)
    save("mount.txt", mnt)
    sysline = [l for l in mnt.splitlines() if " /system " in l or l.strip().endswith(" /system")]
    print("\n[/system 挂载]")
    for l in sysline:
        print("  " + l.strip())
    if not sysline:
        print("  (未单独列出 /system，详见 out/mount.txt)")

    # 6. su 是否存在
    rc, su = sh([ADB, "-s", dev, "shell", "ls -l /system/bin/su /system/xbin/su /system/bin/.ext/su 2>&1"], timeout=20)
    print("\n[su 二进制]")
    print("  " + su.strip().replace("\n", "\n  "))
    save("su.txt", su)

    # 7. 包名清单
    rc, pkgs = sh([ADB, "-s", dev, "shell", "pm list packages -f"], timeout=120)
    save("packages_all.txt", pkgs)
    names = sorted(set(re.findall(r"package:(\S+?)=(\S+)", pkgs)))
    print("\n[包名] 共 %d 个，已存 out/packages_all.txt" % len(names))

    # 分类
    konka = [n for _, n in names if n.startswith("com.konka")]
    third = []
    rc, p3 = sh([ADB, "-s", dev, "shell", "pm list packages -3"], timeout=60)
    for m in re.finditer(r"package:(\S+)", p3):
        third.append(m.group(1))
    save("packages_third.txt", p3)
    print("  com.konka.* : %d 个" % len(konka))
    print("  第三方      : %d 个" % len(third))
    save("packages_konka.txt", "\n".join(konka))

    # 8. 常驻进程
    rc, ps = sh([ADB, "-s", dev, "shell", "ps"], timeout=30)
    save("ps.txt", ps)
    print("\n[进程] 共 %d 行，已存 out/ps.txt" % len(ps.splitlines()))

    # 9. 内存
    rc, mem = sh([ADB, "-s", dev, "shell", "cat /proc/meminfo"], timeout=20)
    save("meminfo.txt", mem)
    for l in mem.splitlines()[:4]:
        print("  " + l)

    # 10. 备份 packages.xml（只读拉取，供回滚比对）
    for p in ["/data/system/packages.xml", "/data/system/packages-stopped.xml"]:
        rc, x = sh([ADB, "-s", dev, "shell", "cat %s 2>&1 | head -c 200000" % p], timeout=60)
        if rc == 0 and "<" in x:
            save(os.path.basename(p), x)
            print("\n[备份] %s -> out/%s (%d 字节)" % (p, os.path.basename(p), len(x)))

    print("\n" + "=" * 70)
    print("体检完成。输出目录: %s" % OUT)
    print("下一步: 把 out/packages_all.txt 发我，我来出精简白名单")
    print("=" * 70)


if __name__ == "__main__":
    main()
