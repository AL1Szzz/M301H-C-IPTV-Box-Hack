# -*- coding: utf-8 -*-
"""远程助手客户端（禁用系统代理）"""
import urllib.request, urllib.parse, sys, json
HOST = "http://192.168.50.52:9999"
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def get(path, timeout=30):
    try:
        r = op.open(HOST + path, timeout=timeout)
        return r.read().decode("utf-8", "ignore")
    except Exception as e:
        return "!!ERR %s: %s" % (path, e)

def cmd(c, timeout=90):
    try:
        req = urllib.request.Request(HOST + "/cmd", data=c.encode("utf-8"))
        return op.open(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception as e:
        return "!!ERR %s" % e

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cmd":
        print(cmd(" ".join(sys.argv[2:])))
    else:
        print(get(sys.argv[1] if len(sys.argv) > 1 else "/status"))
