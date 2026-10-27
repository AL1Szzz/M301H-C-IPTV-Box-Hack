# -*- coding: utf-8 -*-
r"""
终极验证：这个直播软件到底有没有真的在播（声音起来了 = 视频在跑）

三个信号：
  1. audio_flinger 有 ACTIVE 音轨（播视频必有声）
  2. logcat 里有播放器/解码器在工作
  3. 界面上有没有频道名

用法：python tv_playcheck.py
"""
import json
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
PLAY_HINT = ('IJKMEDIA', 'ijkplayer', 'avformat', 'ffmpeg', 'MediaPlayer', 'VideoView',
             'ExoPlayer', 'PLMediaPlayer', 'openVideo', 'onPrepared', 'setDataSource',
             'start playing', 'AudioTrack')


def adb(args, t=120):
    try:
        r = subprocess.run([ADB, '-s', DEV] + args, capture_output=True, timeout=t)
        return (r.stdout + r.stderr).decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR:%s' % e


def main():
    subprocess.run([ADB, 'connect', HOST], capture_output=True, timeout=60)
    time.sleep(2)
    man = json.load(open(REPORT, encoding='utf-8'))
    todo = [m for m in man if m.get('alive')]
    if sys.argv[1:]:
        todo = [m for m in todo if m['pkg'] in sys.argv[1:]]

    for m in todo:
        pkg = m['pkg']
        adb(['shell', 'logcat', '-c'])
        adb(['shell', 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1'], 60)
        time.sleep(28)

        af = adb(['shell', 'dumpsys', 'media.audio_flinger'], 90)
        # 活跃音轨：state=ACTIVE 或者 track 里有该 uid
        uid = adb(['shell', 'dumpsys', 'package', pkg]).strip()
        uidm = re.search(r'userId=(\d+)', uid)
        uid = uidm.group(1) if uidm else ''
        active = af.count('ACTIVE')
        m['audio_active'] = active
        m['uid'] = uid

        log = adb(['shell', 'logcat', '-d'])
        m['play2'] = [l.strip()[:100] for l in log.splitlines()
                      if any(k in l for k in PLAY_HINT)][:3]

        adb(['shell', 'uiautomator', 'dump', '/sdcard/w.xml'], 90)
        local = TMP + '\\' + pkg + '.xml'
        if '\\' not in local:
            pass
        import os
        if os.path.exists(local):
            os.remove(local)
        adb(['pull', '/sdcard/w.xml', local], 120)
        xml = open(local, encoding='utf-8', errors='ignore').read() if os.path.exists(local) else ''
        texts = [t for t in re.findall(r'text="([^"]*)"', xml) if t.strip()]
        m['ui_channels'] = [t for t in texts if any(k in t for k in CHANNEL_HINT)][:10]
        m['ui_texts'] = texts[:40]
        m['usable'] = (active > 0) or bool(m['ui_channels'])

        print('\n%-28s 音轨ACTIVE=%d 频道=%d 播放日志=%d' %
              (pkg, active, len(m['ui_channels']), len(m['play2'])))
        if m['ui_channels']:
            print('   频道: %s' % '、'.join(m['ui_channels'][:6]))
        for p in m['play2'][:2]:
            print('   日志: %s' % p)
        adb(['shell', 'am', 'force-stop', pkg])

    json.dump(man, open(REPORT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('\n' + '=' * 78)
    for m in json.load(open(REPORT, encoding='utf-8')):
        if not m.get('alive'):
            print('  ✗ 删  %-28s 起不来' % m['pkg'])
        elif m.get('usable'):
            print('  ✓ 留  %-28s 有声音/有台' % m['pkg'])
        else:
            print('  ? 留观 %-28s 没测出播放，明天手动试' % m['pkg'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
