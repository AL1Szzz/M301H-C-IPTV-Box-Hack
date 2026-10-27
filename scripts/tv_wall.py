# -*- coding: utf-8 -*-
"""分步走完桌面「换壁纸」流程并验证结果"""
import time, re
from adbX import shell

def texts():
    shell('uiautomator dump /data/local/tmp/wx.xml >/dev/null 2>&1', timeout=40)
    o, _ = shell('cat /data/local/tmp/wx.xml', timeout=30)
    return [m for m in re.findall(r'text="([^"]*)"', o) if m.strip()]

def dump(tag):
    t = texts()
    print('[%s] %s' % (tag, ' | '.join(t[:10])))
    return t

def key(k, wait=2.0):
    shell('input keyevent %d' % k)
    time.sleep(wait)

print('=== 1. 回到桌面 ===')
shell('am start -n app.orchard.tv4/.LauncherActivity >/dev/null 2>&1')
time.sleep(3)
dump('桌面')

print('\n=== 2. 菜单键 -> 应用菜单 -> 桌面设置 ===')
key(82)
for _ in range(5):
    key(20, 1.0)
dump('应用菜单')
key(23, 2.5)

print('\n=== 3. 全局菜单 -> 换壁纸 ===')
for _ in range(6):
    key(20, 1.0)
dump('全局菜单')
key(23, 2.5)

print('\n=== 4. 换壁纸菜单 ===')
t = dump('换壁纸菜单')
if not any('已下载的壁纸' in x for x in t):
    print('!! 没进到换壁纸菜单，中止')
    raise SystemExit(1)

key(23, 3.0)
print('\n=== 5. 壁纸列表 ===')
t = dump('壁纸列表')
if not any('KB' in x for x in t):
    print('!! 壁纸列表没出现，中止')
    raise SystemExit(1)

key(23, 5.0)
print('\n=== 6. 选中第 1 张，等待设置 ===')
time.sleep(4)
dump('设置后')

print('\n=== 7. 验证 ===')
o, _ = shell('cat /data/data/app.orchard.tv4/shared_prefs/at4.xml 2>&1', su=True)
print('at4.xml:', o.strip()[:200] if o.strip() else '(不存在)')
o, _ = shell('ls -la /data/system/users/0/wallpaper* 2>&1', su=True)
print('系统壁纸:', o.strip()[:200] if o.strip() else '(无)')
o, _ = shell("logcat -d -v brief | busybox grep -iE 'tv4|wallpaper|壁纸|Exception' | busybox tail -10", su=True)
print('日志:', o.strip()[:600] if o.strip() else '(无)')
