# -*- coding: utf-8 -*-
"""
AK50 一键串流：设置画质档位 + 自动连接电脑

用法（PowerShell 或 Git Bash）：
    python stream_connect.py                 # 用默认档位 high，连电视串流
    python stream_connect.py --preset medium # 指定档位
    python stream_connect.py --preset low
    python stream_connect.py --quality-only  # 只改参数，不发起串流

档位说明（电视走的是有线网口 eth0，带宽不是瓶颈，瓶颈是 Mali-T720 解码能力）：
    high    1920x1080  60fps  20000 kbps   # 最清晰，老芯片可能吃力
    medium  1920x1080  30fps  12000 kbps   # 推荐起点，清晰且稳
    low     1280x720   30fps   6000 kbps   # 保底，卡顿时用它

注意：
    - 断流排查期曾把码率压到 2500kbps，画质很差；根因已修（冻结崩溃的
      牌照方应用 + 改扩展显示模式），现在可以放心用 medium/high。
    - 电视上必须用 su 改配置（非 root 下改了不生效）。
"""
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEV = '192.168.50.104:5555'
HOST = '192.168.50.104'
PKG = 'com.limelight'
PREF = '/data/data/com.limelight/shared_prefs/com.limelight_preferences.xml'

PRESETS = {
    'high':   {'res': '1920x1080', 'fps': '60', 'kbps': '20000'},
    'medium': {'res': '1920x1080', 'fps': '30', 'kbps': '12000'},
    'low':    {'res': '1280x720',  'fps': '30', 'kbps': '6000'},
}


def adb(args, t=90):
    try:
        r = subprocess.run([ADB, '-s', DEV] + args, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def sh(cmd, t=90):
    """在电视上以 root 执行"""
    return adb(['shell', "su -c '%s'" % cmd], t)


def connect():
    for _ in range(4):
        subprocess.run([ADB, 'connect', HOST], capture_output=True, timeout=60)
        time.sleep(3)
        out = subprocess.run([ADB, 'devices'], capture_output=True, timeout=30)
        if DEV.split(':')[0] in out.stdout.decode('utf-8', 'ignore'):
            return True
    return False


def set_quality(p):
    """写 Moonlight 画质参数。电视没有原生 sed，必须用 busybox sed"""
    cur = sh('grep -E "list_resolution|list_fps|seekbar_bitrate" %s' % PREF)
    print('  改前: %s' % ' / '.join(x.strip() for x in cur.strip().splitlines()[-3:]))

    # 先把三个值都归一到已知形态再替换，避免 sed 找不到
    sh("busybox sed -i 's|<string name=\"list_resolution\">[^<]*</string>|<string name=\"list_resolution\">%s</string>|' %s" % (p['res'], PREF))
    sh("busybox sed -i 's|<string name=\"list_fps\">[^<]*</string>|<string name=\"list_fps\">%s</string>|' %s" % (p['fps'], PREF))
    sh("busybox sed -i 's|<int name=\"seekbar_bitrate_kbps\" value=\"[0-9]*\" />|<int name=\"seekbar_bitrate_kbps\" value=\"%s\" />|' %s" % (p['kbps'], PREF))
    time.sleep(1)

    cur = sh('grep -E "list_resolution|list_fps|seekbar_bitrate" %s' % PREF)
    print('  改后: %s' % ' / '.join(x.strip() for x in cur.strip().splitlines()[-3:]))
    return p['kbps'] in cur


def pc_entry_xy():
    """dump 界面找到电脑条目的中心坐标（方向键焦点不可靠，坐标点击稳）"""
    adb(['shell', 'uiautomator dump /data/local/tmp/pc.xml'])
    xml = adb(['shell', 'cat /data/local/tmp/pc.xml'])
    import re
    for m in re.finditer(r'<node[^>]*text="([^"]{1,})"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml):
        label, x1, y1, x2, y2 = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        if 'AL1Szzz' in label or 'PC' in label or 'DESKTOP' in label.upper():
            return (x1 + x2) // 2, (y1 + y2) // 2, label
    return None, None, None


def start_stream():
    adb(['shell', 'am force-stop', PKG]) if False else adb(['shell', 'am', 'force-stop', PKG])
    time.sleep(2)
    adb(['shell', 'am', 'start', '-n', '%s/.PcView' % PKG])
    time.sleep(8)

    x, y, label = pc_entry_xy()
    if x is None:
        print('  ! 没找到电脑条目，电视可能没发现主机；请确认电脑 Sunshine 正在运行')
        return False
    print('  点击电脑条目「%s」@ (%d,%d)' % (label, x, y))
    adb(['shell', 'input', 'tap', str(x), str(y)])
    time.sleep(6)
    if 'AppView' not in adb(['shell', 'dumpsys window']):
        print('  ! 未进入应用列表')
        return False

    # 应用列表里第一项是 Desktop，直接确认
    adb(['shell', 'input', 'keyevent', '23'])
    time.sleep(10)
    win = adb(['shell', 'dumpsys window'])
    return 'Game' in win


def main():
    preset = 'medium'
    quality_only = False
    args = sys.argv[1:]
    if '--quality-only' in args:
        quality_only = True
    for a in args:
        if a in PRESETS:
            preset = a

    p = PRESETS[preset]
    print('档位 %s: %s %sfps %s kbps' % (preset, p['res'], p['fps'], p['kbps']))

    print('连接电视 %s ...' % HOST)
    if not connect():
        print('连接失败：电视关机 / 网络不通 / ADB 未开（工厂菜单 2008）')
        return 1
    ident = sh('id')
    print('  身份: %s' % ident.strip())
    if 'uid=0' not in ident:
        print('  ! 非 root，改参数会静默失败。请在电视上给 SuperSU 授权')

    print('设置画质 ...')
    if not set_quality(p):
        print('  ! 参数可能没写进去，继续尝试连接')

    if quality_only:
        print('完成（仅改参数）')
        return 0

    print('发起串流 ...')
    ok = start_stream()
    if ok:
        print('已串流：电视现在应该显示电脑画面')
    else:
        print('未成功串流，请在电视上手动：Moonlight → 选 AL1SzzzのPC → Desktop')
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
