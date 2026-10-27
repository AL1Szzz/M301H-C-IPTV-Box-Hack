# -*- coding: utf-8 -*-
import socket
HOST="192.168.50.52"
def http(p, raw):
    try:
        s=socket.socket(); s.settimeout(3); s.connect((HOST,p)); s.sendall(raw)
        d=b""
        while True:
            c=s.recv(4096)
            if not c: break
            d+=c
            if len(d)>3000: break
        s.close(); return d.decode("utf-8","ignore")
    except Exception as e: return "ERR "+str(e)[:40]

print("===== 4008 各种路径 =====")
for path in ("/","/index.html","/api","/status","/info","/version","/diag","/debug","/adb"):
    r=http(4008, ("GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n"%(path,HOST)).encode())
    print("[%s] %s" % (path, r.split("\r\n\r\n")[0].replace("\r\n"," | ")[:200]))

print()
print("===== 4008 RTSP/其他 =====")
for name,raw in [("OPTIONS-rtsp", b"OPTIONS * RTSP/1.0\r\nCSeq: 1\r\n\r\n"),
                 ("POST", b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n")]:
    r=http(4008, raw)
    print("[%s] %s" % (name, r.split("\r\n\r\n")[0].replace("\r\n"," | ")[:200]))
