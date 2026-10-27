# -*- coding: utf-8 -*-
"""盒子部署: 装 AerialTV4 v2 -> 启用菜单键无障碍服务 -> 冻结第二批垃圾应用 -> 验证"""
import subprocess, time

ADB = r"C:/Users/Administrator/Documents/Qoder/2026-10-25/4c19e445/tools-dl/platform-tools/adb.exe"
IP = "192.168.50.52:5555"

def run(*args, t=60):
    try:
        r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=t)
        return ((r.stdout or '') + (r.stderr or '')).strip()
    except Exception as e:
        return 'TIMEOUT ' + str(e)

print(run("connect", IP)); time.sleep(4)
print('== push/install AerialTV4 ==')
print(run("push", r"F:/AK50/04_APK/AerialTV4.apk", "/data/local/tmp/tv4.apk", t=120))
print(run("shell", "pm install -f -r /data/local/tmp/tv4.apk"))
print('== 启用菜单键无障碍服务 ==')
print(run("shell", "settings put secure enabled_accessibility_services app.orchard.tv4/.MenuKeyService"))
print(run("shell", "settings put secure accessibility_enabled 1"))
print(run("shell", "settings get secure enabled_accessibility_services"))
print('== 确认原桌面启用 ==')
print(run("shell", "pm enable com.gitv.launcher"))
print('== 冻结第二批(接口/推广类，保留桌面依赖+点播直播+投屏+语音) ==')
for pkg in ["com.aspirecn.pay.agent",
            "com.aspirecn.push.cmd.client",
            "com.cmcc.autotest",
            "com.cmcc.mid.softdetector",
            "com.ysten.remote.service_JS",
            "com.android.smart.terminal.iptv.aidl",
            "com.chinamobile.activate",
            "com.android.cmcc.cmcclancfg",
            "com.xiaodianshi.tv.yst"]:
    print(pkg, '=>', run("shell", "pm disable " + pkg))
print('== 验证 ==')
print(run("shell", "pm list packages -e | busybox grep -cE 'launcherjs|gitv.launcher'"))
print(run("shell", "pm list packages -d"))
