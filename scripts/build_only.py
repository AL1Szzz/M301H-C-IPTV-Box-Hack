# -*- coding: utf-8 -*-
"""只编译 APK 不安装（用于 U 盘拷到盒子）
用法: build_only.py <项目目录> <输出文件名>
"""
import os, subprocess, sys, glob, shutil

ENV = r'C:\Users\Administrator\Downloads\AK50-Root精简\env'
OUT = r'F:\AK50\04_APK'

PROJ = sys.argv[1] if len(sys.argv) > 1 else r'F:\AK50\03_桌面源码\livetv'
NAME = sys.argv[2] if len(sys.argv) > 2 else 'AKLiveTV.apk'

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
os.makedirs(OUT, exist_ok=True)
dst = os.path.join(OUT, NAME)
shutil.copy(apk, dst)
print('APK: %s  (%d bytes)' % (dst, os.path.getsize(dst)))
