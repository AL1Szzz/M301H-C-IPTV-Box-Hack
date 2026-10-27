# -*- coding: utf-8 -*-
import socket, threading, queue, time
HOST="192.168.50.52"
q=queue.Queue(); res=[]
for p in range(1,10001): q.put(p)
def work():
    while True:
        try: p=q.get_nowait()
        except Exception: return
        s=socket.socket(); s.settimeout(0.6)
        try:
            s.connect((HOST,p)); res.append(p)
        except Exception: pass
        finally: s.close()
ts=[threading.Thread(target=work) for _ in range(300)]
t0=time.time()
for t in ts: t.start()
for t in ts: t.join()
print("耗时 %.1fs  开放端口:" % (time.time()-t0), sorted(res))
