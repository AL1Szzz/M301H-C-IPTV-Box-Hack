# -*- coding: utf-8 -*-
"""启动指定应用 -> 等待 -> uiautomator dump -> 解析可见文本/选中项"""
import sys, re, time, xml.etree.ElementTree as ET
from adbX import shell, run

PKG = sys.argv[1] if len(sys.argv) > 1 else 'com.miaokantv.live'
ACT = sys.argv[2] if len(sys.argv) > 2 else ''
WAIT = int(sys.argv[3]) if len(sys.argv) > 3 else 8

shell('am force-stop %s' % PKG)
time.sleep(1)
if ACT:
    shell('am start -n %s/%s' % (PKG, ACT))
else:
    shell('monkey -p %s -c android.intent.category.LAUNCHER 1' % PKG)
print('launched, waiting %ds ...' % WAIT)
time.sleep(WAIT)

# dump 到 /data/local/tmp（/sdcard 会丢）
shell('rm -f /data/local/tmp/ui.xml')
o, e = shell('uiautomator dump /data/local/tmp/ui.xml', timeout=60)
print('dump:', o.strip()[:200])
o, _ = shell('cat /data/local/tmp/ui.xml')
if not o.strip().startswith('<?xml'):
    print('!! dump 失败:\n', o[:500])
    sys.exit(1)

open(r'F:\AK50\06_系统快照\last_ui.xml', 'w', encoding='utf-8').write(o)
root = ET.fromstring(o.strip())

print('\n--- 当前前台 ---')
o2, _ = shell('dumpsys window windows | grep -E "mCurrentFocus|mFocusedApp"')
print(o2.strip()[:300])

print('\n--- 可见元素 ---')
shown = 0
for n in root.iter('node'):
    t = n.get('text') or ''
    d = n.get('content-desc') or ''
    r = n.get('resource-id') or ''
    b = n.get('bounds') or ''
    if not t and not d:
        continue
    flags = []
    if n.get('selected') == 'true':
        flags.append('SEL')
    if n.get('focused') == 'true':
        flags.append('FOC')
    if n.get('checked') == 'true':
        flags.append('CHK')
    print('%-28s %-14s %-24s %s' % ((t or d)[:28], '|'.join(flags), r.split('/')[-1][:24], b))
    shown += 1
print('共 %d 个可见节点' % shown)
