# -*- coding: utf-8 -*-
"""v4 助手客户端（9998）"""
import urllib.request, sys, os
HOST="http://192.168.50.52:9998"
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(p, timeout=40):
    try: return op.open(HOST+p, timeout=timeout).read().decode("utf-8","ignore")
    except Exception as e: return "!!ERR %s: %s"%(p,e)
def cmd(c, timeout=120):
    try:
        return op.open(urllib.request.Request(HOST+"/cmd", data=c.encode("utf-8")), timeout=timeout).read().decode("utf-8","ignore")
    except Exception as e: return "!!ERR %s"%e
def snap(out):
    d=op.open(HOST+"/shot.jpg", timeout=60).read()
    open(out,"wb").write(d); return len(d)
if __name__=="__main__":
    a=sys.argv[1]
    if a=="cmd": print(cmd(" ".join(sys.argv[2:])))
    elif a=="snap":
        n=snap(sys.argv[2]); print("shot %dB -> %s"%(n,sys.argv[2]))
    else: print(get(a))
