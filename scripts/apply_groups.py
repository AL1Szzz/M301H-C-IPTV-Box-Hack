# -*- coding: utf-8 -*-
"""
按 chnCode 手工映射表给江苏移动 IPTV 117 频道做【中文名 + 分组】，
重写 F:/AK50/07_直播源/js_cmcc_iptv.m3u，并合并进电视直播 assets/live.m3u。
URL 一律沿用现有文件（含 accountinfo，不重新鉴权）。
"""
import re, json

BASE = 'F:/AK50/06_系统快照/盒子/cap/'
M3U  = 'F:/AK50/07_直播源/js_cmcc_iptv.m3u'
LIVE = 'F:/AK50/03_桌面源码/livetv/app/src/main/assets/live.m3u'

# chnCode -> (显示名, 分组)
M = {
 # ---------------- 央视 ----------------
 'G_CCTV-1-HD-265-8M':      ('CCTV-1 综合',        '央视'),
 'G_CCTV-2-HD-265-8M':      ('CCTV-2 财经',        '央视'),
 'G_CCTV-3-HD-265-8M':      ('CCTV-3 综艺',        '央视'),
 'G_CCTV-4-HD-265-8M':      ('CCTV-4 中文国际',    '央视'),
 'G_CCTV-6-HD-265-8M':      ('CCTV-6 电影',        '央视'),
 'G_CCTV-7-HQ':             ('CCTV-7 国防军事',    '央视'),
 'G_CCTV-8-HD-265-5M':      ('CCTV-8 电视剧',      '央视'),
 'G_CCTV-10-HQ':            ('CCTV-10 科教',       '央视'),
 'G_CCTV-11-HQ':            ('CCTV-11 戏曲',       '央视'),
 'HD-8000k-1080P-cctv12':   ('CCTV-12 社会与法',   '央视'),
 'HD-8000k-1080P-cctv14':   ('CCTV-14 少儿',       '少儿·教育'),
 'G_CCTV-15':               ('CCTV-15 音乐',       '央视'),
 'G_CCTV-16-CQ':            ('CCTV-16 奥林匹克',   '央视'),
 'G_CCTV-16-4K':            ('CCTV-16 4K',         '央视'),
 'G_CCTV-17-HD':            ('CCTV-17 农业农村',   '央视'),
 'G_CCTV-9':                ('CCTV-9 纪录',        '纪实·纪录'),
 'G_CCTV-NEWS':             ('CGTN 英语',          '央视'),
 'G_CCTV-4K-HD':            ('CCTV-4K 超高清',     '央视'),
 'G_CCTV-13-HQ':            ('CCTV-13 新闻',       '央视'),
 'G_CCTV-1-AVS-4K264':      ('CCTV-1 4K',          '央视'),
 'G_CCTV-2-AVS-4K264':      ('CCTV-2 4K',          '央视'),
 'G_CCTV-3-AVS-4K264':      ('CCTV-3 4K',          '央视'),
 'G_CCTV-5-4K264':          ('CCTV-5 4K',          '央视'),
 'G_CCTV-6-AVS-4K264':      ('CCTV-6 4K',          '央视'),
 'G_CCTV-8-AVS-4K264':      ('CCTV-8 4K',          '央视'),
 'G_CCTV-5-HD-265-5M':      ('CCTV-5 体育',        '体育'),
 'G_CCTV-5PLUS-HD-265-5M':  ('CCTV-5+ 赛事',       '体育'),
 'G_CCTV-2-CQ':             ('CCTV-2 财经(备)',    '央视'),
 'G_FENGYUNYY-CQ':          ('风云音乐',           '央视'),
 'G_CCTV-WENHUA-CQ':        ('央视文化',           '央视'),
 # ---------------- 卫视 ----------------
 'G_JIANGSU-HD-265-8M':     ('江苏卫视',           '卫视'),
 'G_ZHEJIANG-HD-265-8M':    ('浙江卫视',           '卫视'),
 'G_BEIJING-HD-265-8M':     ('北京卫视',           '卫视'),
 'G_HUNAN-HD-265-8M':       ('湖南卫视',           '卫视'),
 'G_DONGFANG-HD-265-8M':    ('东方卫视',           '卫视'),
 'G_ANHUI-HD-265-8M':       ('安徽卫视',           '卫视'),
 'G_GUANGDONG-HD-265-8M':   ('广东卫视',           '卫视'),
 'G_HEILONGJIANG-HD-265-8M':('黑龙江卫视',         '卫视'),
 'G_JILIN-CQ':              ('吉林卫视',           '卫视'),
 'G_SHENZHEN-HD-265-8M':    ('深圳卫视',           '卫视'),
 'G_SHANDONG-HD-265-8M':    ('山东卫视',           '卫视'),
 'G_TIANJIN-HD-265-8M':     ('天津卫视',           '卫视'),
 'G_HUBEI-HD-265-8M':       ('湖北卫视',           '卫视'),
 'G_CHONGQING-CQ':          ('重庆卫视',           '卫视'),
 'G_JIANGXI-CQ':            ('江西卫视',           '卫视'),
 'G_LIAONING-HD-265-8M':    ('辽宁卫视',           '卫视'),
 'DNWS':                    ('东南卫视',           '卫视'),
 'HD-8000k-1080P-lvyoustv': ('旅游卫视',           '卫视'),
 'G_SICHUAN-CQ':            ('四川卫视',           '卫视'),
 'GXWS':                    ('广西卫视',           '卫视'),
 'G_HENAN-CQ':              ('河南卫视',           '卫视'),
 'G_HEBEI-CQ':              ('河北卫视',           '卫视'),
 'G_GUIZHOU-CQ':            ('贵州卫视',           '卫视'),
 'G_GANSU':                 ('甘肃卫视',           '卫视'),
 # ---------------- 体育 ----------------
 'G_DIYICJ-HQ':             ('第一财经',           '卫视'),
 'G_TAIQIU-CQ':             ('央视台球',           '体育'),
 'G_BINGQIKJ-CQ':           ('兵器科技',           '纪实·纪录'),
 'G_QIMO':                  ('汽摩运动',           '体育'),
 'G_MIGUJCQS':              ('咪咕精彩赛事',       '体育'),
 'miguaoyun1-AVS':          ('咪咕竞技',           '体育'),
 'miguaoyun01-AVS-4K01':    ('咪咕4K',             '体育'),
 'HD-8000k-1080P-miguaoyun2':('睛彩竞技',          '体育'),
 # ---------------- 影视·剧场 ----------------
 'G_DIYIJC-CQ':             ('第一剧场',           '影视·剧场'),
 'G_FENGYUNJC-CQ':          ('风云剧场',           '影视·剧场'),
 'G_HUAIJIUJC-CQ':          ('怀旧剧场',           '影视·剧场'),
 'COSHD-4000k-1080P-wenxin':('剧场·温馨',          '影视·剧场'),
 'COSHD-4000k-1080P-htwy':  ('剧场·htwy',          '影视·剧场'),
 'COSHD-4000k-1080P-fbdry': ('剧场·fbdry',         '影视·剧场'),
 'COSHD-4000k-1080P-fczx':  ('剧场·fczx',          '影视·剧场'),
 'COSHD-4000k-1080P-xiaorizi':('剧场·小日子',      '影视·剧场'),
 'COSHD-4000k-1080P-xxnwnw':('剧场·xxnwnw',        '影视·剧场'),
 'COSHD-1500k-1080P-wlgsj': ('剧场·wlgsj',         '影视·剧场'),
 'COSHD-4000k-1080P-lyjdhc':('剧场·lyjdhc',        '影视·剧场'),
 'mengzhongdnph':           ('梦中的那片海',       '影视·剧场'),
 'cos-liebing':             ('猎冰',               '影视·剧场'),
 'cos-yonganmeng':          ('永安梦',             '影视·剧场'),
 'cos-yanhuorenjia':        ('烟花人家',           '影视·剧场'),
 'manchangdjj':             ('漫长的季节',         '影视·剧场'),
 # ---------------- 纪实·纪录 ----------------
 'HD-8000k-1080P-beijingjishi':('北京纪实',        '纪实·纪录'),
 'G_SHIJIEDL-CQ':           ('世界地理',           '纪实·纪录'),
 'G_HUANGQIUQIGUAN':        ('环球奇观',           '纪实·纪录'),
 # ---------------- 少儿·教育 ----------------
 'G_CETV-ZQJY-CQ':          ('CETV 早期教育',      '少儿·教育'),
 'G_GUOXUE':                ('国学频道',           '少儿·教育'),
 'G_ZHONGXUESHENG':         ('中学生频道',         '少儿·教育'),
 # ---------------- 生活·其他 ----------------
 'G_FENGSHANGZQ-CQ':        ('风尚频道',           '生活·其他'),
 'G_NVXINGSS-CQ':           ('女性时尚',           '生活·其他'),
 'G_DIANSHIZN-CQ':          ('电视指南',           '生活·其他'),
}
# GITV-JS-N → 江苏·本地
def jsname(code):
    n = code.split('-')[-1]
    return ('江苏·专业频道' + n, '江苏·本地')
for i in [1,2,3,7,9,11,12,13,16,17,18,19,21,22,24,25,26,28,33,39,40,41,42,43,44,46,47,48,49,50,68]:
    M['GITV-JS-%d' % i] = jsname('GITV-JS-%d' % i)

def main():
    # PLTV id -> chnCode（来自 probe_union.py 的探测结果）
    id2code = {}
    for code, pltv, union in json.load(open(BASE + 'union_map.json')):
        if pltv and pltv.isdigit():
            id2code[pltv] = code

    lines = [l.rstrip() for l in open(M3U, encoding='utf8') if l.strip()]
    out = ['#EXTM3U']
    missing = []
    i = 0
    n = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('#EXTINF'):
            nxt = lines[i+1] if i+1 < len(lines) else ''
            code = None
            # URL 里的 PLTV id 反查 chnCode
            if nxt.startswith('http'):
                pm = re.search(r'/PLTV/\d+/\d+/(\d+)/', nxt)
                if pm and pm.group(1) in id2code:
                    code = id2code[pm.group(1)]
            if code is None or code not in M:
                m = re.match(r'#EXTINF:-1 tvg-name="([^"]+)"', l)
                missing.append(m.group(1) if m else l[:50])
                out.append(l)
                if nxt.startswith('http'): out.append(nxt); i += 1
                i += 1
                continue
            disp, grp = M[code]
            out.append('#EXTINF:-1 tvg-name="%s" group-title="%s",%s' % (disp, grp, disp))
            if nxt.startswith('http'):
                out.append(nxt); i += 1
            n += 1
        i += 1
    open(M3U, 'w', encoding='utf8').write('\n'.join(out) + '\n')
    print('重写完成: %d 个频道带映射, 未识别 %d' % (n, len(missing)))
    for x in missing: print('  ?', x)

if __name__ == '__main__':
    main()
