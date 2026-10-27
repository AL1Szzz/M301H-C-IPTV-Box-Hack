# -*- coding: utf-8 -*-
import socket, struct, sys
HOST="192.168.50.52"
def mk(cmd, arg0, arg1, data=b""):
    magic = 0xFFFFFFFF
    c = 0
    for b in cmd: c = (c<<8) | b
    magic ^= c
    chk = sum(data) & 0xFFFFFFFF
    return struct.pack("<6I", c, arg0, arg1, len(data), chk, magic) + data
def probe(port):
    try:
        s=socket.socket(); s.settimeout(3); s.connect((HOST,port))
        s.sendall(mk(b"CNXN", 0x01000000, 4096, b"host::probe\x00"))
        d=s.recv(256); s.close()
        return d
    except Exception as e:
        return b"ERR "+str(e).encode()
for p in (5555,6666,8080,30016,5037):
    d = probe(p)
    print(p, "->", d[:100])
