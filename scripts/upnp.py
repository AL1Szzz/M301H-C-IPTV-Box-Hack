# -*- coding: utf-8 -*-
import socket
HOST="192.168.50.52"
s=socket.socket(); s.settimeout(4); s.connect((HOST,1566))
s.sendall(("GET / HTTP/1.1\r\nHost: %s:1566\r\nConnection: close\r\n\r\n"%HOST).encode())
d=b""
while True:
    c=s.recv(4096)
    if not c: break
    d+=c
s.close()
t=d.decode("utf-8","ignore")
print(t[t.find("\r\n\r\n")+4:][:2200])
