# -*- coding: utf-8 -*-
r"""
TV 软件批量体检 + 装机（给 KKTV AK50 / Android 4.4.4 用）

用法：
    python test_tv_apps.py                      # 只体检，不安装
    python test_tv_apps.py --dir E:\download\tv # 指定 APK 目录（递归子目录）
    python test_tv_apps.py --install            # 体检 + 自动装兼容的
    python test_tv_apps.py --install --launch   # 体检 + 装 + 逐个启动看会不会秒退

流程：
    1. 扫描目录下所有 .apk
    2. 用 aapt 读出 package / minSdk(SDK版本) / ABI / 是否 TV(leanback)
    3. 按这台电视的 Android 4.4.4 (API 19) 分级：
         能装   minSdk <= 19
         悬     minSdk 20~25（可强行装，多半跑不起来）
         装不了 minSdk >= 26
    4. --install 时把「能装」的推到电视，--launch 再逐个启动并抓崩溃

注意：
    - aapt 遇到中文路径会报 Illegal byte sequence，脚本会先复制到英文临时目录。
    - 电视必须开机且 ADB 可连（工厂菜单 2008 开 ADB）。
"""
import os
import re
import shutil
import subprocess
import sys
import time
import glob
import json

APK_DIR = r'C:\Users\Administrator\Downloads\TV软件'


def pick_opt(name):
    """取 --name 后面的值，没有就返回 None"""
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def pick_dir():
    """支持 --dir <path> 覆盖默认目录"""
    d = pick_opt('--dir')
    if d:
        return os.path.abspath(d)
    return APK_DIR
TMP = r'C:\Users\Administrator\Downloads\apktmp\tvtest'
AAPT = r'C:\Users\Administrator\Downloads\AK50-Root精简\env\android-sdk\build-tools\33.0.1\aapt.exe'
ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
HOST = '192.168.50.104'
DEV = HOST + ':5555'

# 这台电视：Android 4.4.4 = API 19
DEVICE_SDK = 19


def adb(args, t=90):
    try:
        r = subprocess.run([ADB, '-s', DEV] + args, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def connect():
    for _ in range(4):
        subprocess.run([ADB, 'connect', HOST], capture_output=True, timeout=60)
        time.sleep(3)
        out = subprocess.run([ADB, 'devices'], capture_output=True, timeout=30)
        if HOST in out.stdout.decode('utf-8', 'ignore'):
            return True
    return False


def probe(apk, display=None):
    """用 aapt 读 APK 元信息。返回 dict"""
    info = {'file': display or os.path.basename(apk), 'path': apk,
            'pkg': '?', 'minSdk': '?', 'abi': '?', 'label': '?', 'tv': False, 'ok': False}
    try:
        r = subprocess.run([AAPT, 'dump', 'badging', apk], capture_output=True, timeout=120)
        out = (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        info['err'] = str(e)
        return info
    if 'package:' not in out:
        info['err'] = 'aapt 读不出（文件损坏或不是 APK）'
        return info
    m = re.search(r"package: name='([^']+)'.*?versionCode='([^']*)'.*?versionName='([^']*)'", out, re.S)
    if m:
        info['pkg'], info['verCode'], info['verName'] = m.group(1), m.group(2), m.group(3)
    m = re.search(r"sdkVersion:'([^']*)'", out)
    if m:
        info['minSdk'] = m.group(1)
    m = re.search(r"targetSdkVersion:'([^']*)'", out)
    if m:
        info['targetSdk'] = m.group(1)
    m = re.search(r"native-code: (.*)", out)
    if m:
        # 一行里可能有多个 ABI：native-code: 'armeabi-v7a' 'arm64-v8a'
        info['abis'] = re.findall(r"'([^']*)'", m.group(1)) or [m.group(1).strip()]
        info['abi'] = ', '.join(info['abis'])
    else:
        info['abis'] = []
        info['abi'] = '纯 Java(无 so)'
    m = re.search(r"application-label:?'([^']*)'", out)
    if m:
        info['label'] = m.group(1)
    m = re.search(r"launchable-activity: name='([^']*)'", out)
    if m:
        info['launch'] = m.group(1)
    if 'android.software.leanback' in out or 'LEANBACK_LAUNCHER' in out:
        info['tv'] = True
    info['ok'] = True
    return info


# 这台电视的 CPU 支持的 ABI（32 位 ARM）。没有任一匹配就装不上。
DEVICE_ABIS = ('armeabi', 'armeabi-v7a')


def verdict(i):
    if not i['ok']:
        return 'ERR'
    abis = i.get('abis') or []
    if abis and not any(a in DEVICE_ABIS for a in abis):
        return '装不了'
    try:
        s = int(i['minSdk'])
    except Exception:
        return '?'
    if s <= DEVICE_SDK:
        return '能装'
    if s <= 25:
        return '悬'
    return '装不了'


def main():
    install = '--install' in sys.argv
    launch = '--launch' in sys.argv

    apk_dir = pick_dir()
    os.makedirs(TMP, exist_ok=True)
    apks = sorted(glob.glob(os.path.join(apk_dir, '**', '*.apk'), recursive=True))
    if not apks:
        print('目录里没有 APK：%s' % apk_dir)
        print('请先把网盘里的软件下载到这里')
        return 1

    print('目录：%s' % apk_dir)
    print('=' * 78)
    print('扫描到 %d 个 APK（目标设备：Android 4.4.4 / API %d）' % (len(apks), DEVICE_SDK))
    print('=' * 78)

    results = []
    seen = {}          # 包名 -> 结果（去重，保留版本高的）
    for idx, src in enumerate(apks):
        # 复制到英文路径，规避 aapt 中文路径报错
        tmp = os.path.join(TMP, 'app%02d.apk' % idx)
        shutil.copy2(src, tmp)
        i = probe(tmp, display=os.path.relpath(src, apk_dir))
        i['verdict'] = verdict(i)
        i['src'] = src
        results.append(i)
        p = i['pkg']
        if p == '?':
            continue
        if p not in seen or int(i.get('verCode') or 0) > int(seen[p].get('verCode') or 0):
            seen[p] = i
        else:
            i['dup'] = True

    for i in results:
        print('\n[%s] %s%s' % (i['verdict'], i['file'],
                               '   （重复包，已有更新版：%s）' % seen[i['pkg']]['file'] if i.get('dup') else ''))
        if not i['ok']:
            print('     ! %s' % i.get('err', '未知错误'))
            continue
        print('     包名 : %s' % i['pkg'])
        print('     版本 : %s (%s)' % (i.get('verName', '?'), i.get('verCode', '?')))
        print('     最低SDK: %s  (4.4.4=19)' % i['minSdk'])
        print('     架构 : %s' % i['abi'])
        print('     电视适配: %s' % ('是(leanback)' if i['tv'] else '否（要用遥控器可能不顺）'))
        if i['verdict'] == '装不了':
            if i.get('abis') and not any(a in DEVICE_ABIS for a in i['abis']):
                print('     -> CPU 架构不匹配：只有 %s，这台是 32 位 armeabi-v7a' % i['abi'])
            else:
                print('     -> 需要 Android %s 以上，这台 4.4.4 装不了' % i['minSdk'])

    # 去重后、判定可装的最终清单
    todo = [i for i in results if i['verdict'] == '能装' and not i.get('dup')]

    # --stage <outdir>：把去重后能装的拷成英文文件名，方便后面 adb install
    stage = pick_opt('--stage')
    if stage:
        os.makedirs(stage, exist_ok=True)
        for f in glob.glob(os.path.join(stage, '*.apk')):
            os.remove(f)
        manifest = []
        for n, i in enumerate(todo, 1):
            dst = os.path.join(stage, '%02d_%s.apk' % (n, i['pkg']))
            shutil.copy2(i['src'], dst)
            manifest.append({'apk': os.path.basename(dst), 'pkg': i['pkg'],
                             'ver': i.get('verName', '?'), 'tv': i['tv'],
                             'origin': i['file']})
        mp = os.path.join(stage, 'manifest.json')
        with open(mp, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print('\n已整理 %d 个到：%s' % (len(manifest), stage))
        print('清单：%s' % mp)
        return 0

    if not install:
        print('\n（只体检未安装。加 --install 自动装兼容的）')
        return 0

    print('\n' + '=' * 78)
    if not connect():
        print('电视连不上：确认已开机、ADB 已开（信源→模拟电视→菜单→2008）')
        return 1
    print('电视已连接')

    print('准备安装 %d 个（已去掉重复包）' % len(todo))
    for i in todo:
        r = adb(['install', '-r', i['src']], 180)
        ok = 'Success' in r or 'success' in r
        i['installed'] = ok
        print('  %-12s %s' % ('OK' if ok else '失败', i['file']))
        if not ok:
            print('      %s' % r.strip().replace('\n', ' ')[:150])

    if launch:
        print('\n逐个启动验证（每个 10 秒，看会不会秒退）...')
        for i in todo:
            if not i.get('installed'):
                continue
            pkg = i['pkg']
            adb(['logcat', '-c'])
            adb(['shell', 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1'], 60)
            time.sleep(10)
            top = adb(['shell', 'dumpsys', 'window'])
            alive = pkg in top
            crash = adb(['shell', 'logcat', '-d'])
            bad = ('FATAL EXCEPTION' in crash) or ('force finishing' in crash)
            print('  %-40s 启动=%s 崩溃=%s' % (i['file'], '成功' if alive else '未到前台', '有' if bad else '无'))

    print('\n完成。冻结脚本：python freeze_safe.py %s --freeze' % HOST)
    return 0


if __name__ == '__main__':
    sys.exit(main())
