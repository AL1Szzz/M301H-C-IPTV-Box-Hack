# -*- coding: utf-8 -*-
"""抓指定关键字的 logcat（电视端过滤，去掉噪声）"""
import sys, time
from adbX import shell

KW = sys.argv[1] if len(sys.argv) > 1 else 'diypi'
SECS = int(sys.argv[2]) if len(sys.argv) > 2 else 20

shell('logcat -c')
print('cleared, capturing %ds ...' % SECS)
time.sleep(SECS)
# 电视端 grep（busybox 有）；排除常见噪声
o, _ = shell(
    "logcat -d -v brief | busybox grep -iE '%s' | busybox grep -viE "
    "'WindowManager|ActivityManager: Start proc|SMB|smb|WindowState|InputDispatcher'"
    % KW, timeout=60)
print(o[-6000:])
