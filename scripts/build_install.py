# -*- coding: utf-8 -*-
"""编译 APK 并安装到电视（强制内部存储）
用法:
  build_install.py                       # 默认编译 livetv
  build_install.py <项目目录> <包名> <输出名>
"""
import os, subprocess, sys, glob, shutil

ENV = r'C:\Users\Administrator\Downloads\AK50-Root精简\env'
ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
OUT = r'F:\AK50\04_APK'

# 默认：AK直播
PROJ = r'F:\AK50\03_桌面源码\livetv'
PKG = 'app.orchard.livetv'
NAME = 'AKLiveTV.apk'

if len(sys.argv) >= 4:
    PROJ, PKG, NAME = sys.argv[1], sys.argv[2], sys.argv[3]

java_home = os.path.join(ENV, 'jdk17', 'jdk-17.0.13+11')
gradle = os.path.join(ENV, 'gradle-7.5.1', 'bin', 'gradle.bat')

e = dict(os.environ)
e['JAVA_HOME'] = java_home
e['ANDROID_HOME'] = os.path.join(ENV, 'android-sdk')
e['ANDROID_SDK_ROOT'] = e['ANDROID_HOME']
e['JAVA_TOOL_OPTIONS'] = ('-Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=7897 '
                          '-Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=7897 '
                          '-Dfile.encoding=UTF-8')

print('=== 编译 %s ===' % PROJ)
p = subprocess.run([gradle, 'assembleDebug', '--console=plain'],
                   cwd=PROJ, env=e, capture_output=True, text=True, timeout=900)
out = (p.stdout or '') + (p.stderr or '')
if p.returncode != 0:
    print('\n'.join(out.splitlines()[-35:]))
    print('!! 编译失败 rc=%d' % p.returncode)
    sys.exit(1)
print('BUILD OK')

apks = glob.glob(os.path.join(PROJ, 'app', 'build', 'outputs', 'apk', 'debug', '*.apk'))
if not apks:
    print('!! 没找到 APK'); sys.exit(1)
apk = apks[0]
print('APK: %s (%d bytes)' % (apk, os.path.getsize(apk)))

# 安装：push 到 /data/local/tmp 再 su -c pm install -f -r
subprocess.run([ADB, 'shell', 'am force-stop ' + PKG], capture_output=True, timeout=30)
tmp = '/data/local/tmp/' + NAME.replace('.apk', '') + '.apk'
r = subprocess.run([ADB, 'push', apk, tmp], capture_output=True, text=True, timeout=120)
print('push:', (r.stdout or '').strip()[:100], (r.stderr or '').strip()[:150])
r = subprocess.run([ADB, 'shell', 'su -c "pm install -f -r %s"' % tmp],
                   capture_output=True, text=True, timeout=180)
print('install:', (r.stdout or '').strip()[:200], (r.stderr or '').strip()[:150])

os.makedirs(OUT, exist_ok=True)
dst = os.path.join(OUT, NAME)
shutil.copy(apk, dst)
print('已保存 ->', dst)
