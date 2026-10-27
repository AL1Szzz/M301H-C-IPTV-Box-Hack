# -*- coding: utf-8 -*-
import socket
HOST="192.168.50.52"
PAY = [
 ("空等待",  None),
 ("回车",    b"\r\n\r\n"),
 ("HTTP1.0", b"GET / HTTP/1.0\r\n\r\n"),
 ("help",    b"help\n"),
 ("shell",   b"shell:/n"),
]
for p in (6666,8080):
    for name,pl in PAY:
        try:
            s=socket.socket(); s.settimeout(4); s.connect((HOST,p))
            if pl: s.sendall(pl)
            try:
                d=s.recv(512)
                if not d: d=b"<EMPTY>"
            except Exception:
                d=b"<NO-REPLY>"
            s.close()
            print("%s %-8s -> %r" % (p,name,d[:120]))
        except Exception as e:
            print("%s %-8s -> ERR %s" % (p,name,str(e)[:40]))
