# -*- coding: utf-8 -*-
"""
解冻/冻结盒子应用。自动选通道：
  1) ADB root（192.168.50.52:5555）
  2) stbtool2 HTTP 助手（9998）+ factory_test run_cmd 后门
用法:
  unfreeze.py enable <包名> [包名...]     解冻（恢复可用）
  unfreeze.py disable <包名> [包名...]    冻结
  unfreeze.py status <包名> [包名...]     查看状态
不带包名时，enable 使用下面的「安全恢复集」。
"""
import sys, os, subprocess, socket

BOX = "192.168.50.52:5555"
ADB = r"C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe"

# 「我的应用」页可能依赖的组件（转圈时优先恢复这些）
SAFE_RESTORE = [
    "com.aspirecn.jshdc.appstore",
    "com.aspirecn.jshdc.personalcenter",
    "com.aspirecn.jshdc.appusage",
    "com.aspire.hdc.msg.agent",
    "com.chinamobile.sdk.upgrade",
]


def port_open(port, host="192.168.50.52", t=1.5):
    try:
        s = socket.create_connection((host, port), t)
        s.close()
        return True
    except Exception:
        return False


def run_adb(cmd):
    p = subprocess.run([ADB, "-s", BOX, "shell", cmd],
                       capture_output=True, text=True, timeout=60)
    return (p.stdout or "").strip()


def run_http(cmd):
    """经 stbtool2 的 /cmd 转发；要 root 就用 factory_test 后门"""
    import urllib.request
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        return op.open(urllib.request.Request(
            "http://192.168.50.52:9998/cmd", data=cmd.encode("utf-8")),
            timeout=90).read().decode("utf-8", "ignore")
    except Exception as e:
        return "!!ERR %s" % e


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    act = args[0]
    pkgs = args[1:] or (SAFE_RESTORE if act == "enable" else [])
    if not pkgs:
        print("需要指定包名")
        return

    # 选通道
    subprocess.run([ADB, "connect", BOX], capture_output=True, timeout=20)
    use_adb = port_open(5555)
    print("通道: %s" % ("ADB root" if use_adb else "HTTP 助手(9998)"))

    for p in pkgs:
        if act == "status":
            cmd = "pm path %s; dumpsys package %s 2>/dev/null | grep -m1 enabled" % (p, p)
        else:
            cmd = "pm %s %s" % (act, p)
        out = run_adb(cmd) if use_adb else run_http(
            "factory_test run_cmd '%s'" % cmd)
        print("%-45s %s" % (p, out.replace("\n", " | ")[:110]))


if __name__ == "__main__":
    main()
