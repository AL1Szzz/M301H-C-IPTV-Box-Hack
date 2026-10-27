# -*- coding: utf-8 -*-
"""给电视/盒子配 WiFi（走 wpa_cli，不需要点界面）。

用法：
  python tv_wifi.py scan              # 扫描并列出周围 WiFi
  python tv_wifi.py connect 802 密码   # 连接指定 WiFi
  python tv_wifi.py status            # 查看当前连接状态
"""
import re
import sys
import time

from adbX import shell

SOCK = '/data/misc/wifi/sockets'
IFACE = 'wlan0'


def wc(args, timeout=40):
    o, e = shell('wpa_cli -i %s -p %s %s' % (IFACE, SOCK, args), timeout=timeout, su=True)
    return (o or '') + (e or '')


def status():
    out = wc('status')
    d = {}
    for line in out.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            d[k.strip()] = v.strip()
    return d


def do_scan():
    print('触发扫描...')
    wc('scan', timeout=30)
    for i in range(8):
        time.sleep(3)
        out = wc('scan_results', timeout=30)
        rows = [l for l in out.splitlines() if '\t' in l]
        if rows:
            print('%-34s %-6s %-5s %s' % ('SSID', '信号', '加密', '频率'))
            seen = set()
            for r in rows:
                p = r.split('\t')
                if len(p) < 5:
                    continue
                bssid, freq, sig, flags, ssid = p[0], p[1], p[2], p[3], p[4]
                if ssid in seen:
                    continue
                seen.add(ssid)
                print('%-34s %-6s %-5s %s' % (ssid, sig, flags[:4], freq))
            return
    print('没扫到（或扫描未完成）')


def connect(ssid, psk):
    print('当前网络列表:')
    out = wc('list_networks', timeout=30)
    nets = {}
    for line in out.splitlines():
        m = re.match(r'^(\d+)\t([^\t]*)\t', line)
        if m:
            nets[int(m.group(1))] = m.group(2)
    for nid, s in nets.items():
        print('  #%d  %s' % (nid, s))
        if s == ssid:
            print('  已存在该网络，先移除')
            wc('remove_network %d' % nid, timeout=30)

    out = wc('add_network', timeout=30)
    m = re.search(r'(\d+)', out.strip().splitlines()[-1] if out.strip() else '')
    if not m:
        print('add_network 失败:', out)
        return
    nid = m.group(1)
    print('新建网络 id=%s' % nid)

    # wpa_cli 要求字符串参数自带双引号，所以这里用单引号把双引号保住
    print(wc("set_network %s ssid '\"%s\"'" % (nid, ssid), timeout=30).strip())
    print(wc("set_network %s psk '\"%s\"'" % (nid, psk), timeout=30).strip())
    print(wc('set_network %s key_mgmt WPA-PSK' % nid, timeout=30).strip())
    print(wc('set_network %s priority 10' % nid, timeout=30).strip())
    print(wc('select_network %s' % nid, timeout=30).strip())
    print(wc('enable_network %s' % nid, timeout=30).strip())
    print(wc('reconnect', timeout=30).strip())
    print(wc('save_config', timeout=30).strip())

    print('等待连接...')
    for i in range(10):
        time.sleep(3)
        st = status()
        state = st.get('wpa_state', '')
        ip = st.get('ip_address', '')
        print('  %2ds  state=%-12s ssid=%-12s ip=%s'
              % ((i + 1) * 3, state, st.get('ssid', '-'), ip or '-'))
        if state == 'COMPLETED' and ip:
            print('\n连接成功: SSID=%s  IP=%s' % (st.get('ssid'), ip))
            return ip
    print('\n未能完成连接，最后状态: %s' % status())


def show_status():
    st = status()
    for k in ('wpa_state', 'ssid', 'bssid', 'ip_address', 'key_mgmt'):
        if k in st:
            print('  %-12s %s' % (k, st[k]))
    o, _ = shell('busybox ifconfig wlan0 | busybox head -4', timeout=30, su=True)
    print(o)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd == 'scan':
        do_scan()
    elif cmd == 'connect' and len(sys.argv) >= 4:
        connect(sys.argv[2], sys.argv[3])
    else:
        show_status()
