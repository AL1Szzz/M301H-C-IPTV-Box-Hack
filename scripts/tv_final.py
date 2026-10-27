# -*- coding: utf-8 -*-
r"""
AK50 收尾脚本：补装 + 逐个启动实测 + 卸载不能用的 + 禁自启 + 电视关机

用法：
    python tv_final.py check     # 只补装 + 启动测试，出报告（不动手）
    python tv_final.py clean     # 按报告卸载起不来的 + 禁掉自启组件
    python tv_final.py off       # 电视关机
"""
import json
import os
import shutil
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
HOST = '192.168.50.104'
DEV = HOST + ':5555'
STAGE = r'C:\Users\Administrator\Downloads\AK50-Root精简\apks\tv2'
REPORT = r'C:\Users\Administrator\Downloads\AK50-Root精简\tv2_report.json'


def adb(args, t=120):
    try:
        r = subprocess.run([ADB, '-s', DEV] + args, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def connect():
    subprocess.run([ADB, 'connect', HOST], capture_output=True, timeout=60)
    time.sleep(2)
    return DEV in subprocess.run([ADB, 'devices'], capture_output=True,
                                 timeout=30).stdout.decode('utf-8', 'ignore')


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if not connect():
        print('电视连不上')
        return 1

    man = json.load(open(os.path.join(STAGE, 'manifest.json'), encoding='utf-8'))

    if mode == 'off':
        print(adb(['shell', 'reboot', '-p']).strip() or '已发关机指令')
        return 0

    # 1. 确认哪些装上了
    out = adb(['shell', 'pm', 'list', 'packages', '-3'])
    installed = set(l.replace('package:', '').strip() for l in out.splitlines() if l.startswith('package:'))
    for m in man:
        m['installed'] = m['pkg'] in installed

    # 2. 补装（源文件取原始下载目录，先复制到英文临时路径再推，规避中文路径）
    os.makedirs(os.path.join(STAGE, 'tmp'), exist_ok=True)
    for m in man:
        if m['installed']:
            continue
        src = os.path.join(r'E:\download\tv', m['origin'])
        tmp = os.path.join(STAGE, 'tmp', m['apk'])
        if os.path.exists(tmp):
            os.remove(tmp)
        shutil.copy2(src, tmp)
        r = adb(['install', '-r', tmp], 300)
        m['installed'] = 'Success' in r
        m['install_msg'] = r.strip().replace('\n', ' ')[:120]
        print('%-26s 补装=%s %s' % (m['pkg'], 'OK' if m['installed'] else '失败',
                                    '' if m['installed'] else m.get('install_msg', '')))

    if mode != 'check':
        pass

    # 3. 逐个启动实测
    for m in man:
        if not m['installed']:
            m['alive'] = False
            m['crash'] = True
            m['note'] = '没装上'
            continue
        pkg = m['pkg']
        adb(['shell', 'logcat', '-c'])
        adb(['shell', 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1'], 60)
        time.sleep(12)
        win = adb(['shell', 'dumpsys', 'window'])
        m['alive'] = pkg in win
        log = adb(['shell', 'logcat', '-d'])
        m['crash'] = ('FATAL EXCEPTION' in log) or ('force finishing' in log) or ('has died' in log)
        # 有没有真的在播：看有没有播放器/网络相关迹象
        net = any(k in log for k in ('MediaPlayer', 'IjkMediaPlayer', 'ExoPlayer', 'play', 'OkHttp', 'retrofit'))
        m['net'] = net
        err = [l for l in log.splitlines() if ' E ' in l and pkg in l][:3]
        m['err'] = err
        adb(['shell', 'am', 'force-stop', pkg])

    print('\n' + '=' * 78)
    print('%-28s %-6s %-6s %-6s %s' % ('包名', '装上', '前台', '崩溃', '备注'))
    print('=' * 78)
    for m in man:
        print('%-28s %-6s %-6s %-6s %s' % (
            m['pkg'], '是' if m['installed'] else '否',
            '是' if m.get('alive') else '否',
            '有' if m.get('crash') else '无',
            m.get('note', '')))
        for e in m.get('err', [])[:2]:
            print('      %s' % e.strip()[:110])

    json.dump(man, open(REPORT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('\n报告：%s' % REPORT)

    if mode == 'clean':
        print('\n--- 清理 ---')
        for m in man:
            bad = (not m['installed']) or m.get('crash') or (not m.get('alive'))
            if bad:
                r = adb(['uninstall', m['pkg']], 120)
                print('卸载 %-28s %s' % (m['pkg'], 'OK' if 'Success' in r else r.strip()[:60]))
            else:
                # 保留的：禁掉开机自启接收器
                pkg = m['pkg']
                d = adb(['shell', 'dumpsys', 'package', pkg])
                comps = []
                cur = None
                for l in d.splitlines():
                    ls = l.strip()
                    if ls.startswith('Receiver Resolver Table') or 'receiver' in ls and ls.endswith(':'):
                        pass
                    if 'android.intent.action.BOOT_COMPLETED' in ls:
                        # 上一行的组件名形如 com.x/.BootReceiver filter 1234
                        comps.append(cur)
                    if ls.startswith(pkg) and '/' in ls:
                        cur = ls.split()[0]
                comps = [c for c in comps if c and '/' in c]
                for c in comps:
                    adb(['shell', 'su', '-c', 'pm', 'disable', c])
                print('保留 %-28s 禁用自启组件 %d 个' % (pkg, len(comps)))
        # 收尾：确保没留后台
        adb(['shell', 'am', 'kill-all'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
