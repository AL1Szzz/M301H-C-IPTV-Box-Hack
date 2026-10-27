# -*- coding: utf-8 -*-
"""一次性把文件喂给连上来的客户端"""
import socket, sys, threading, time
HOST="0.0.0.0"; PORT=int(sys.argv[1]); FILE=sys.argv[2]
s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
s.bind((HOST,PORT)); s.listen(1)
print("listening %d -> %s" % (PORT, FILE), flush=True)
c,a=s.accept()
print("peer", a, flush=True)
d=open(FILE,"rb").read()
c.sendall(d); print("sent", len(d), flush=True)
time.sleep(1); c.close(); s.close()
