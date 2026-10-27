# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, sys, os
HOST="http://192.168.50.52:9999"
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
path=sys.argv[1]; out=sys.argv[2]
url=HOST+"/dl?path="+urllib.parse.quote(path,safe="")
d=op.open(url,timeout=180).read()
open(out,"wb").write(d)
print("OK %d bytes -> %s" % (len(d), out))
