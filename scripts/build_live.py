# -*- coding: utf-8 -*-
"""合并直播源 -> 生成电视可用的 live.m3u
优先 http（电视 Android 4.4 对 TLS1.3 支持差，https 容易握手失败）
"""
import re, io, os

BASE = r'F:\AK50\05_直播源'

def parse(path):
    """返回 [(title, group, url), ...]"""
    items = []
    with io.open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f]
    cur = None
    for l in lines:
        if l.startswith('#EXTINF'):
            m = re.search(r'group-title="([^"]*)"', l)
            group = m.group(1) if m else '其他'
            name = l.split(',')[-1].strip()
            cur = (name, group)
        elif l.startswith('http'):
            if cur:
                items.append((cur[0], cur[1], l.strip()))
            cur = None
    return items


# 1) 已验证可达（电视端 busybox wget 实测 100%）
# 顺序按实测流畅度排：绍兴(流畅，vo 帧稳定) > 延边 > 浙江(1080p 会卡缓冲)
verified = [
    ('绍兴新闻综合', '已验证', 'http://live.shaoxing.com.cn/video/s10001-sxhb/index.m3u8'),
    ('延边卫视', '已验证', 'http://live.ybtvyun.com/video/s10006-44f040627ca1/index.m3u8'),
    ('浙江卫视', '已验证', 'http://ali-m-l.cztv.com/channels/lantian/channel01/1080p.m3u8'),
]

out = []
out.append('#EXTM3U')
seen = set()


def add(name, group, url):
    if url in seen:
        return
    seen.add(url)
    out.append('#EXTINF:-1 tvg-name="%s" group-title="%s",%s' % (name, group, name))
    out.append(url)


for n, g, u in verified:
    add(n, g, u)

# 2) gather.m3u 里的 http 源（移动咪咕 OTT，公网 IPv4）
cnt_http = 0
for path in ['gather.m3u']:
    p = os.path.join(BASE, path)
    if not os.path.exists(p):
        continue
    for n, g, u in parse(p):
        if u.startswith('http://'):
            add(n, '公网', u)
            cnt_http += 1

# 3) ipv6.m3u 单独出一份（家里目前没有公网 IPv6，先不用）
v6_out = ['#EXTM3U']
cnt_v6 = 0
p = os.path.join(BASE, 'ipv6.m3u')
if os.path.exists(p):
    for n, g, u in parse(p):
        v6_out.append('#EXTINF:-1 tvg-name="%s" group-title="央视频道",%s' % (n, n))
        v6_out.append(u)
        cnt_v6 += 1
with io.open(os.path.join(BASE, 'ipv6_only.m3u'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(v6_out) + '\n')

dst = os.path.join(BASE, 'live.m3u')
with io.open(dst, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')

n_total = sum(1 for l in out if l.startswith('http'))
print('已生成 %s' % dst)
print('  http 公网源: %d' % cnt_http)
print('  主列表频道: %d' % n_total)
print('  IPv6 备用(单独文件): %d' % cnt_v6)
