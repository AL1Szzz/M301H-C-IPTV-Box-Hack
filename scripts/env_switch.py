# -*- coding: utf-8 -*-
"""AK50 相关环境开关：用完关掉、需要时再打开。

用法:
  python env_switch.py status   # 查看当前状态
  python env_switch.py on       # 打开：启动 Sunshine 串流服务
  python env_switch.py off      # 关闭：停 Sunshine + 杀掉 adb 守护进程

说明：Sunshine 服务已改为「手动」启动，不会随开机自启；
      需要串流时 on，用完 off 即可。
      注意：不用 sc.exe（被安全策略拦截），一律走 PowerShell cmdlet。
"""
import json
import subprocess
import sys

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'
PS = ['powershell', '-NoProfile', '-NonInteractive', '-Command']


def run(args, timeout=90):
    p = subprocess.run(args, capture_output=True, timeout=timeout)
    out = (p.stdout or b'') + (p.stderr or b'')
    return out.decode('utf-8', 'ignore').strip()


def ps(cmd):
    return run(PS + [cmd])


# ServiceControllerStatus / ServiceStartMode 经 ConvertTo-Json 会变成数字
SVC_STATUS = {1: '已停止', 2: '启动中', 3: '停止中', 4: '运行中',
              5: '继续中', 6: '暂停中', 7: '已暂停'}
SVC_START = {0: 'Boot', 1: 'System', 2: '自动', 3: '手动', 4: '禁用'}


def service_state():
    """返回 (是否运行中, 启动类型文本)"""
    out = ps('Get-Service -Name SunshineService -ErrorAction SilentlyContinue | '
             'Select-Object Status,StartType | ConvertTo-Json')
    if not out or 'Status' not in out:
        return None, None
    try:
        d = json.loads(out)
        st, sm = d.get('Status'), d.get('StartType')
        # 枚举可能是数字也可能是字符串
        running = (st == 4) or (str(st).upper() == 'RUNNING')
        start = SVC_START.get(sm, sm if isinstance(sm, str) else str(sm))
        return running, start
    except Exception:
        return None, None


def adb_count():
    out = ps('(Get-Process -Name adb -ErrorAction SilentlyContinue | Measure-Object).Count')
    try:
        return int(out.strip().splitlines()[-1])
    except Exception:
        return -1


def do_status():
    running, st = service_state()
    if running is None:
        print('Sunshine 服务 : 未安装 / 查不到')
    else:
        print('Sunshine 服务 : %s（启动类型 %s）' % (SVC_STATUS.get(4 if running else 1), st))
    print('adb 守护进程 : %s' % adb_count())


def do_on():
    print(ps('Start-Service -Name SunshineService -ErrorAction SilentlyContinue; '
             '(Get-Service SunshineService).Status') or '（无输出，可能已启动）')
    do_status()


def do_off():
    print(ps('Stop-Service -Name SunshineService -Force -ErrorAction SilentlyContinue; '
             '(Get-Service SunshineService).Status') or '（无输出，可能已停止）')
    print(run([ADB, 'kill-server']) or 'adb 已停止')
    do_status()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    {'on': do_on, 'off': do_off, 'status': do_status}.get(cmd, do_status)()
