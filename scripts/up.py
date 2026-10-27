# -*- coding: utf-8 -*-
"""上传文件到 stbtool2 的 /up/<name> 端点"""
import sys, urllib.request
HOST = "http://192.168.50.52:9998"
fn = sys.argv[1]
name = sys.argv[2] if len(sys.argv) > 2 else fn.split("/")[-1].split("\\")[-1]
data = open(fn, "rb").read()
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
r = op.open(urllib.request.Request(HOST + "/up/" + name, data=data), timeout=120)
print(r.read().decode("utf-8", "ignore"))
