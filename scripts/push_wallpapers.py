# -*- coding: utf-8 -*-
"""把电脑上的壁纸推进电视桌面的私有壁纸目录"""
import os, glob
from adbX import run, shell

SRC = r'F:\AK50\07_壁纸'
REMOTE_DIR = '/data/data/app.orchard.tv4/files/wallpapers'

files = sorted(glob.glob(os.path.join(SRC, '*.jpg')) + glob.glob(os.path.join(SRC, '*.png')))
if not files:
    print('壁纸目录为空:', SRC)
    raise SystemExit(1)

o, _ = shell('mkdir -p %s && chmod 755 %s && ls -d %s' % (REMOTE_DIR, REMOTE_DIR, REMOTE_DIR), su=True)
print('目录:', o.strip())

ok = 0
for f in files:
    name = os.path.basename(f)
    tmp = '/data/local/tmp/' + name
    run(['push', f, tmp], timeout=90)
    o, _ = shell('cp %s %s/%s && chmod 644 %s/%s' % (tmp, REMOTE_DIR, name, REMOTE_DIR, name), su=True)
    o2, _ = shell('ls -la %s/%s' % (REMOTE_DIR, name), su=True)
    if name in o2:
        ok += 1
        print('OK  %s  (%d KB)' % (name, os.path.getsize(f) // 1024))
    else:
        print('FAIL', name, o.strip()[:100])

o, _ = shell('ls -la %s/' % REMOTE_DIR, su=True)
print('\n=== 电视壁纸目录 ===')
print(o.strip())
print('成功 %d/%d' % (ok, len(files)))
