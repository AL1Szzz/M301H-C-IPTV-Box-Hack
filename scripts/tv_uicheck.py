# -*- coding: utf-8 -*-
r"""
screencap 在这台 4.4 电视上不可用（恒 0 字节），改用 uiautomator dump 抓界面文本，
判断每个直播软件到底有没有台、是不是在报错。

用法：python tv_uicheck.py
"""
import json
import os
import re
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
HOST = '192.168.50.104'
DEV = HOST + ':5555'
TMP = r'C:\Users\Administrator\Downloads\apktmp\ui'
REPORT = r'C:\Users\Administrator\Downloads\AK50-Root精简\tv2_report.json'

CHANNEL_HINT = ('CCTV', 'cctv', '央视', '卫视', '湖南', '浙江', '江苏', '东方', '北京',
                '广东', '山东', '河南', '湖北', '安徽', '天津', '重庆', '少儿', '新闻',
                '综合', '高清', '频道', '体育', '电影', '电视剧')
ERR_HINT = ('失败', '错误', '无法', '异常', '加载中', '暂无', '没有数据', '服务器',
            '重试', '网络', '已停止', '未响应', '过期', '请联系', 'Error', 'error')
PLAY_HINT = ('MediaPlayer', 'IjkMediaPlayer', 'ExoPlayer', 'ijkplayer', 'start playing',
             'onPrepared', 'setDataSource', 'VideoView', 'PLMediaPlayer', 'prepareAsync')


def adb(args, t=120):
    try:
        r = subprocess.run([ADB, '-s', DEV] + args, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def main():
    subprocess.run([ADB, 'connect', HOST], capture_output=True, timeout=60)
    time.sleep(2)
    os.makedirs(TMP, exist_ok=True)
    man = json.load(open(REPORT, encoding='utf-8'))
    todo = [m for m in man if m.get('alive')]
    only = sys.argv[1:]
    if only:
        todo = [m for m in todo if m['pkg'] in only]

    for m in todo:
        pkg = m['pkg']
        adb(['shell', 'logcat', '-c'])
        adb(['shell', 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1'], 60)
        time.sleep(16)
        adb(['shell', 'uiautomator', 'dump', '/sdcard/w.xml'], 90)
        local = os.path.join(TMP, pkg + '.xml')
        if os.path.exists(local):
            os.remove(local)
        adb(['pull', '/sdcard/w.xml', local], 120)
        xml = ''
        if os.path.exists(local):
            xml = open(local, encoding='utf-8', errors='ignore').read()
        texts = [t for t in re.findall(r'text="([^"]*)"', xml) if t.strip()]
        ch = [t for t in texts if any(k in t for k in CHANNEL_HINT)]
        er = [t for t in texts if any(k in t for k in ERR_HINT)]
        log = adb(['shell', 'logcat', '-d'])
        play = [l.strip()[:100] for l in log.splitlines() if any(k in l for k in PLAY_HINT)][:2]
        m['ui_texts'] = texts[:40]
        m['ui_channels'] = ch[:10]
        m['ui_err'] = er[:5]
        m['play'] = play
        m['usable'] = bool(ch) and not er
        print('\n%-28s 台=%d  报错=%d  播放迹象=%s' % (pkg, len(ch), len(er), '有' if play else '无'))
        print('   频道样例: %s' % ('、'.join(ch[:6]) if ch else '（没读到频道名）'))
        if er:
            print('   报错文本: %s' % '、'.join(er[:4]))
        if play:
            for p in play:
                print('   播放: %s' % p)
        adb(['shell', 'am', 'force-stop', pkg])

    json.dump(man, open(REPORT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('\n' + '=' * 78)
    print('可用判定：')
    for m in man:
        if not m.get('alive'):
            print('  ✗ %-28s 起不来' % m['pkg'])
        elif m.get('usable'):
            print('  ✓ %-28s 有台 %d 个，无报错' % (m['pkg'], len(m.get('ui_channels', []))))
        else:
            print('  ? %-28s 台 %d，报错 %s' % (m['pkg'], len(m.get('ui_channels', [])),
                                                m.get('ui_err', [])[:2]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
