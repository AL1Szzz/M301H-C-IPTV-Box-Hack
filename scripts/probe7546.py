# -*- coding: utf-8 -*-
import socket, hashlib, re
HOST="192.168.50.52"; PORT=7546
def raw(req):
    try:
        s=socket.socket(); s.settimeout(3); s.connect((HOST,PORT)); s.sendall(req)
        d=b""
        while True:
            c=s.recv(4096)
            if not c: break
            d+=c
            if len(d)>6000: break
        s.close(); return d.decode("utf-8","ignore")
    except Exception as e: return "ERR "+str(e)[:40]

first = raw(("GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n"%HOST).encode())
print("===== 原始 401 响应 =====")
print(first[:900])
