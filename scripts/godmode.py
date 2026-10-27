# -*- coding: utf-8 -*-
"""
godmode.py —— Android "上帝模式"(My Android Tools 同款原理) 组件管理器

原理: PackageManager.setComponentEnabledSetting()
  - 列出 APK manifest 里的四大组件(含 manifest 里 enabled=false 的隐藏入口)
  - pm disable <pkg>/<comp>  隐藏入口 / 掐掉广告、推送、统计、静默升级组件
  - pm enable  <pkg>/<comp>  打开厂商隐藏的入口
  - am start -n <pkg>/<act>  直达任意 Activity(哪怕它没有 launcher 图标)

比"冻结整个应用"精细得多: 只掐组件, 宿主应用照常跑, 不会把桌面搞转圈。

用法:
  python godmode.py list <pkg>                 列出组件 + 启用状态
  python godmode.py list <pkg> --all           含 receiver/service/provider
  python godmode.py ad <pkg>                   只看"广告/推送/统计"类可禁候选
  python godmode.py disable <pkg> <comp...>    禁用组件(支持多个/关键词)
  python godmode.py enable  <pkg> <comp...>    启用组件
  python godmode.py launch <pkg>/<act>         直达 Activity
  python godmode.py launch <pkg>               直达该包 launchable activity
  python godmode.py state <pkg>                只看运行时 disabled/enabled 列表

设备: -d 192.168.50.52:5555(默认, 盒子) / 192.168.50.17(电视)
"""
import os, re, sys, subprocess, argparse

ADB = r"C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe"
AAPT = r"F:\AK50\05_工具\aapt.exe"
CACHE = r"F:\AK50\boxbak\apks"

# 可禁用候选关键词(命中即高亮). 保守: 只标不自动禁
AD_KW = [
    "ad", "ads", "advert", "banner", "splash", "welcome", "guide",
    "pay", "purchase", "order", "vip", "recharge", "mall", "shop",
    "push", "stat", "track", "report", "log", "monitor", "apm",
    "upgrade", "update", "ota", "install", "silence",
    "test", "demo", "debug", "mock", "sandbox",
    "umeng", "bugly", "talkingdata", "yingyongbao", "getui", "jpush", "xiaomi",
    "game", "edu", "grade", "parent", "child", "weather", "screen",
]

COMP_TAG = {"activity": "ACT", "activity-alias": "ALS",
            "service": "SRV", "receiver": "RCV", "provider": "PRV"}


def sh(dev, cmd, timeout=60):
    p = subprocess.run([ADB, "-s", dev, "shell", cmd], capture_output=True,
                       text=True, errors="replace", timeout=timeout)
    return p.stdout or ""


def sh_out(cmd, timeout=120):
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                       timeout=timeout, shell=True)
    return p.stdout or ""


def apk_path(dev, pkg):
    out = sh(dev, "pm path %s" % pkg)
    m = re.search(r"package:(.+)", out)
    return m.group(1).strip() if m else None


def pull_apk(dev, pkg):
    os.makedirs(CACHE, exist_ok=True)
    local = os.path.join(CACHE, pkg + ".apk")
    if os.path.exists(local) and os.path.getsize(local) > 10000:
        return local
    remote = apk_path(dev, pkg)
    if not remote:
        return None
    subprocess.run([ADB, "-s", dev, "pull", remote, local],
                   capture_output=True, timeout=180)
    return local if os.path.exists(local) else None


def parse_manifest(apk):
    """aapt dump xmltree -> [(type, name, enabled_from_manifest)]"""
    out = sh_out('"%s" dump xmltree "%s" AndroidManifest.xml' % (AAPT, apk))
    pkg = ""
    m = re.search(r'package="([^"]+)"', out)
    if m:
        pkg = m.group(1)
    comps, cur, cur_enabled = [], None, None
    for line in out.splitlines():
        s = line.strip()
        me = re.match(r"E: (activity|activity-alias|service|receiver|provider)\b", s)
        if me:
            cur = me.group(1)
            cur_enabled = None
            continue
        if s.startswith("E: ") and cur:
            # 进入子元素, 结束当前组件的 name 采集区不影响
            pass
        ma = re.search(r'A: android:name\(0x[0-9a-f]+\)="([^"]*)"', s)
        if ma and cur and cur_enabled is None:
            name = ma.group(1)
            if name.startswith("."):
                name = pkg + name
            elif "." not in name:
                name = pkg + "." + name
            comps.append((COMP_TAG[cur], name, None))
            cur = None
            continue
        meb = re.search(r'A: android:enabled\(0x[0-9a-f]+\)="([^"]*)"', s)
        if meb and comps:
            comps[-1] = (comps[-1][0], comps[-1][1],
                         meb.group(1).lower() in ("true", "0xffffffff"))
    return pkg, comps


def runtime_state(dev, pkg):
    """解析 dumpsys package: 返回 (disabled_set, enabled_set, app_enabled)"""
    out = sh(dev, "dumpsys package %s" % pkg, timeout=90)
    dis, ena = set(), set()
    app_enabled = True
    app_seen = False
    mode = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("disabledComponents:"):
            mode = "d"
            continue
        if s.startswith("enabledComponents:"):
            mode = "e"
            continue
        if re.match(r"^[A-Za-z]", s) and ":" in s and not s.startswith("com."):
            mode = None
        m = re.match(r"^User \d+:.*enabled=(\d)", s)
        if m and app_seen is False:
            app_enabled = (m.group(1) == "1")
            app_seen = True   # 后续 "Hidden system packages" 段里的旧版包不算
        if mode and re.match(r"^[a-zA-Z][\w.$\-]+$", s):
            (dis if mode == "d" else ena).add(s)
    return dis, ena, app_enabled


def is_ad_candidate(name):
    low = name.lower()
    return any(k in low for k in AD_KW)


def do_list(dev, pkg, show_all=False, only_ad=False):
    apk = pull_apk(dev, pkg)
    if not apk:
        print("[!] 拿不到 APK: %s" % pkg)
        return
    mpkg, comps = parse_manifest(apk)
    dis, ena, app_en = runtime_state(dev, pkg)
    if not app_en:
        print("[!] 注意: 应用整体已被冻结(enabled=0)")
    print("== %s  组件 %d 个 ==" % (mpkg, len(comps)))
    print("%-4s %-58s %-9s %s" % ("类型", "组件", "状态", "建议"))
    print("-" * 100)
    for tag, name, men in comps:
        if not show_all and tag in ("SRV", "RCV", "PRV"):
            continue
        short = name[len(mpkg):] if name.startswith(mpkg) else name
        if name in dis:
            st, mark = "DISABLED", ""
        elif name in ena:
            st, mark = "ENABLED*", ""
        elif men is False:
            st, mark = "HIDDEN", "  <- manifest 里默认关闭(可 pm enable 打开)"
        else:
            st, mark = "on", "  <= 可禁" if is_ad_candidate(short) else ""
        if only_ad and not (is_ad_candidate(short) and st == "on"):
            continue
        if only_ad and tag in ("SRV", "RCV", "PRV"):
            continue
        print("%-4s %-58s %-9s%s" % (tag, short[:58], st, mark))
    if dis:
        print("\n[已禁用组件] %d 个" % len(dis))
    return comps, dis, ena


def do_set(dev, pkg, comps, enable):
    verb = "enable" if enable else "disable"
    for c in comps:
        n = c if "/" in c else (pkg + "/" + c)
        if "/" not in n.split("/", 1)[1] and not n.startswith(pkg + "."):
            pass
        full = n if n.startswith(pkg + "/") else pkg + "/" + (c if not c.startswith(".") else c)
        out = sh(dev, "pm %s %s" % (verb, full), timeout=40)
        ok = ("new state" in out.lower()) or (out.strip() == "") or ("enabled" in out.lower())
        print("%-6s %-62s %s" % (verb, full[10:][:62], out.strip().replace("\n", " ")[:40] or "OK"))


def do_launch(dev, spec):
    if "/" in spec:
        out = sh(dev, "am start -n %s" % spec, timeout=40)
    else:
        out = sh(dev, "monkey -p %s -c android.intent.category.LAUNCHER 1" % spec, timeout=40)
    print(out.strip()[:500])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("pkg", nargs="?")
    ap.add_argument("comps", nargs="*")
    ap.add_argument("-d", "--device", default="192.168.50.52:5555")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    subprocess.run([ADB, "connect", a.device], capture_output=True)
    if a.cmd == "list":
        do_list(a.device, a.pkg, show_all=a.all)
    elif a.cmd == "ad":
        do_list(a.device, a.pkg, only_ad=True)
    elif a.cmd == "state":
        dis, ena, en = runtime_state(a.device, a.pkg)
        print("app enabled=%s" % en)
        print("disabled(%d):" % len(dis))
        for x in sorted(dis):
            print("  " + x)
        print("enabled*(%d):" % len(ena))
        for x in sorted(ena):
            print("  " + x)
    elif a.cmd in ("disable", "enable"):
        do_set(a.device, a.pkg, a.comps, a.cmd == "enable")
    elif a.cmd == "launch":
        do_launch(a.device, a.pkg)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
