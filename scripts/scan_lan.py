# -*- coding: utf-8 -*-
"""扫描局域网 192.168.50.0/24，列出在线设备（IP + MAC + 主机名）。"""
import concurrent.futures as cf
import re
import subprocess
import sys

SUBNET = sys.argv[1] if len(sys.argv) > 1 else '192.168.50'


def ping(ip):
    try:
        r = subprocess.run(['ping', '-n', '1', '-w', '300', ip],
                           capture_output=True, timeout=3)
        return ip, (r.returncode == 0)
    except Exception:
        return ip, False


def arp_table():
    out = subprocess.run(['arp', '-a'], capture_output=True, timeout=20)
    txt = out.stdout.decode('gbk', 'ignore') or out.stdout.decode('utf-8', 'ignore')
    tbl = {}
    for m in re.finditer(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F\-:]{17})\s+(\S+)', txt):
        tbl[m.group(1)] = (m.group(2), m.group(3))
    return tbl


def main():
    ips = ['%s.%d' % (SUBNET, i) for i in range(1, 255)]
    alive = []
    with cf.ThreadPoolExecutor(max_workers=60) as ex:
        for ip, ok in ex.map(ping, ips):
            if ok:
                alive.append(ip)
    tbl = arp_table()
    print('在线 %d 台：' % len(alive))
    print('%-16s %-20s %s' % ('IP', 'MAC', '类型'))
    for ip in sorted(alive, key=lambda x: [int(p) for p in x.split('.')]):
        mac, typ = tbl.get(ip, ('-', '-'))
        print('%-16s %-20s %s' % (ip, mac, typ))


if __name__ == '__main__':
    main()
