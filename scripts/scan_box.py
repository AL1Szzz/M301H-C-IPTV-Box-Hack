# -*- coding: utf-8 -*-
import socket, subprocess, sys
HOST = "192.168.50.52"
PORTS = [5555,5554,5037,30016,5000,6666,8888,9999,23,2323,8080]
def alive(ip):
    r = subprocess.run(["ping","-n","2","-w","800",ip],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return r.returncode == 0
print("在线:", alive(HOST))
for p in PORTS:
    s = socket.socket(); s.settimeout(0.8)
    try:
        s.connect((HOST,p))
        banner=""
        try:
            s.settimeout(1.2); banner = s.recv(64).decode("utf-8","ignore")
        except Exception: pass
        print("%-6s 开放  %r" % (p, banner[:60]))
    except Exception:
        print("%-6s 关闭" % p)
    finally:
        s.close()
