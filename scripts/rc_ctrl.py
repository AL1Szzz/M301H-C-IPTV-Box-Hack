# -*- coding: utf-8 -*-
"""远程截屏 + 按键"""
import sys, time, subprocess, os
from rc_client import cmd, HOST
import urllib.request, urllib.parse
OUT = r"F:/AK50/06_系统快照/盒子"
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
KEY = {"up":19,"down":20,"left":21,"right":22,"ok":23,"back":4,"home":3,"menu":82,"volup":24,"voldown":25,"power":26}
def key(*ks):
    for k in ks:
        c = KEY.get(k, k)
        try: c = int(c)
        except: pass
        print(cmd("input keyevent %s" % c), end="")
        time.sleep(0.6)
def snap(name="snap"):
    cmd("sleep 1; /system/bin/screencap -p /data/local/s.png")
    url = HOST + "/dl?path=" + urllib.parse.quote("/data/local/s.png", safe="")
    d = op.open(url, timeout=120).read()
    p = os.path.join(OUT, name + ".png")
    open(p, "wb").write(d)
    print("截图 %dB -> %s" % (len(d), p))
if __name__ == "__main__":
    for a in sys.argv[1:]:
        if a.startswith("snap"):
            snap(a[5:] if len(a) > 4 else "snap")
        else:
            key(a)
