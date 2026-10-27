# -*- coding: utf-8 -*-
r"""
给 FongMi 设置远程接口（不依赖 /sdcard），然后导航到直播页看频道有没有加载
用法：python tv_set_api.py <接口URL>
"""
import os
import re
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
DEV = '192.168.50.104:5555'
PKG = 'com.fongmi.android.tv'
TMP = r'C:\Users\Administrator\Downloads\apktmp\ui'


def sh(a, t=90):
    try:
        r = subprocess.run([ADB, '-s', DEV] + a, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def dump(name):
    sh(['shell', 'uiautomator', 'dump', '/data/local/tmp/%s.xml' % name])
    local = os.path.join(TMP, name + '.xml')
    if os.path.exists(local):
        os.remove(local)
    subprocess.run([ADB, '-s', DEV, 'pull', '/data/local/tmp/%s.xml' % name, local],
                   capture_output=True, timeout=120)
    if not os.path.exists(local):
        return ''
    with open(local, encoding='utf-8', errors='ignore') as f:
        return f.read()


def texts_of(xml):
    return [t for t in re.findall(r'text="([^"]*)"', xml) if t.strip()]


def main():
    api = sys.argv[1] if len(sys.argv) > 1 else 'http://xhztv.top/xhz'
    subprocess.run([ADB, 'connect', '192.168.50.104:5555'], capture_output=True, timeout=60)
    os.makedirs(TMP, exist_ok=True)

    sh(['shell', 'am', 'force-stop', PKG])
    time.sleep(2)
    sh(['shell', 'monkey', '-p', PKG, '-c', 'android.intent.category.LAUNCHER', '1'])
    time.sleep(10)
    print('9978:', sh(['shell', 'netstat -tln | grep 9978']).strip() or '(未监听)')

    import urllib.parse
    import urllib.request
    data = urllib.parse.urlencode({'do': 'api', 'url': api}).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            'http://192.168.50.104:9978/action', data=data), timeout=20)
        print('提交接口 %s -> %s' % (api, r.read().decode('utf-8', 'ignore')[:60]))
    except Exception as e:
        print('提交失败:', e)
        return 1

    time.sleep(35)
    x = dump('s1')
    print('首页:', ' | '.join(texts_of(x)[:12]))

    # 导航：右键一次跳到"推送"，再左移三格到"直播"，确定
    sh(['shell', 'input', 'keyevent', '22'])
    time.sleep(1.5)
    for _ in range(3):
        sh(['shell', 'input', 'keyevent', '21'])
        time.sleep(1.2)
    sel = re.findall(r'<node[^>]*text="([^"]*)"[^>]*selected="true"', dump('s2'))
    print('选中:', sel[:3])
    if sel and sel[-1] != '直播':
        step = 1 if sel[-1] in ('点播', '影视') else -1
        for _ in range(2):
            sh(['shell', 'input', 'keyevent', '22' if step == 1 else '21'])
            time.sleep(1.2)
            sel = re.findall(r'<node[^>]*text="([^"]*)"[^>]*selected="true"', dump('s3'))
            print('  移到:', sel[:3])
            if sel and sel[-1] == '直播':
                break
    sh(['shell', 'input', 'keyevent', '66'])
    time.sleep(30)
    x = dump('s4')
    ts = texts_of(x)
    print('直播页文本(%d): %s' % (len(ts), ' | '.join(ts[:40]) if ts else '(空)'))
    ch = [t for t in ts if re.search(r'CCTV|卫视|央视|湖南|浙江|江苏|东方|北京|广东|山东|凤凰|综合', t)]
    print('识别到频道:', len(ch), ch[:10])
    return 0


if __name__ == '__main__':
    sys.exit(main())
