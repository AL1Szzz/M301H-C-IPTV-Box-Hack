# -*- coding: utf-8 -*-
"""生成 TVBox/FongMi 格式的配置接口 JSON"""
import json, io, os

BASE = r'F:\AK50\05_直播源'
HOST = 'http://192.168.50.213:8000'

cfg = {
    'lives': [
        {'name': '公网直播', 'type': 0, 'url': HOST + '/live.m3u'},
        {'name': 'IPv6备用', 'type': 0, 'url': HOST + '/ipv6_only.m3u'},
    ],
    'sites': [],
    'spider': '',
    'wallpaper': '',
}

p = os.path.join(BASE, 'config.json')
with io.open(p, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)
print('已生成', p)
print(json.dumps(cfg, ensure_ascii=False, indent=2))
