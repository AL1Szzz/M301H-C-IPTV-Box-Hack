# -*- coding: utf-8 -*-
import socket
HOST="192.168.50.52"
for p in (8080,6666):
    print("="*20, p)
    try:
        s=socket.socket(); s.settimeout(3); s.connect((HOST,p))
        req=(b"GET / HTTP/1.1\r\nHost: %s\r\nUser-Agent: curl/8\r\nConnection: close\r\n\r\n" % HOST.encode())
        s.sendall(req)
        buf=b""
        while True:
            d=s.recv(4096)
            if not d: break
            buf+=d
            if len(buf)>4000: break
        s.close()
        print(buf[:1200].decode("utf-8","ignore"))
    except Exception as e:
        print("ERR", e)
