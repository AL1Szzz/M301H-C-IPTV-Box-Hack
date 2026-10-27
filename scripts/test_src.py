# -*- coding: utf-8 -*-
"""批量测试直播源连通性（禁用系统代理，直连）。"""
import io, os, sys, socket, urllib.request

TIMEOUT = 8
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]


def test(u):
    try:
        r = opener.open(u, timeout=TIMEOUT)
        body = r.read(400)
        return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, b''
    except Exception as e:
        return 0, str(e).encode()[:80]


def run(urls, label=''):
    print('=== %s ===' % (label or '测试'))
    ok = []
    for u in urls:
        st, body = test(u)
        mark = 'OK ' if st == 200 else '   '
        head = body.decode('utf-8', 'ignore').replace('\n', ' ')[:70]
        print('%s%-4s %s' % (mark, st, u[:78]))
        if st == 200 and head:
            print('      -> %s' % head)
            ok.append(u)
    print('可用 %d / %d' % (len(ok), len(urls)))
    return ok


if __name__ == '__main__':
    JS = 'http://ott.js.chinamobile.com/PLTV/3/224/%s/index.m3u8'
    IDS = {
        'CCTV-1综合': '3221226316', 'CCTV-2财经': '3221226993', 'CCTV-3综艺': '3221227481',
        'CCTV-4中文国际': '3221227378', 'CCTV-5体育': '3221227401', 'CCTV-5+赛事': '3221227381',
        'CCTV-6电影': '3221227301', 'CCTV-7国防军事': '3221227314', 'CCTV-8电视剧': '3221227204',
        'CCTV-9纪录': '3221227614', 'CCTV-10科教': '3221227317', 'CCTV-11戏曲': '3221227524',
        'CCTV-12社会与法': '3221227637', 'CCTV-13新闻': '3221227601', 'CCTV-14少儿': '3221227201',
        'CCTV-15音乐': '3221227538', 'CCTV-17农业农村': '3221227578',
    }
    urls = [JS % i for i in IDS.values()]
    ok = run(urls, '江苏移动 域名形式 ott.js.chinamobile.com')

    print()
    ips = ['223.110.245.145', '223.110.245.149', '223.110.245.151',
           '223.110.245.153', '223.110.245.161', '223.110.243.146']
    u2 = ['http://%s/ott.js.chinamobile.com/PLTV/3/224/3221226316/index.m3u8' % i for i in ips]
    run(u2, '江苏移动 IP 直连形式（CCTV1）')
