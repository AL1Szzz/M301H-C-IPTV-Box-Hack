# -*- coding: utf-8 -*-
import socket, struct
HOST="192.168.50.52"
PORTS=[1566,2010,4008,6666,7000,7546,8080,8733]
def mk(cmd,arg0,arg1,data=b""):
    c=0
    for b in cmd: c=(c<<8)|b
    magic=(0xFFFFFFFF ^ c) & 0xFFFFFFFF
    return struct.pack("<6I",c,arg0,arg1,len(data),sum(data)&0xFFFFFFFF,magic)+data
def once(p, pl, to=3.0):
    try:
        s=socket.socket(); s.settimeout(to); s.connect((HOST,p))
        if pl: s.sendall(pl)
        try:
            d=s.recv(300)
            if not d: d=b"<EMPTY>"
        except Exception: d=b"<NO-REPLY>"
        s.close(); return d
    except Exception as e:
        return b"ERR "+str(e)[:35].encode()
for p in PORTS:
    http = once(p, b"GET / HTTP/1.0\r\nHost: box\r\n\r\n")
    adb  = once(p, mk(b"CNXN",0x01000000,4096,b"host::\x00"))
    print("---- %d" % p)
    print("  HTTP:", http[:150])
    print("  ADB :", adb[:150])
