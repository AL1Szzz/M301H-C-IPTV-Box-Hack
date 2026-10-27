# -*- coding: utf-8 -*-
"""AK50 相关环境开关：用完关掉、需要时再打开。

用法:
  python env_switch.py status   # 查看当前状态
  python env_switch.py on       # 打开：启动 Sunshine 串流服务
  python env_switch.py off      # 关闭：停 Sunshine + 杀掉 adb 守护进程

说明：Sunshine 服务已改为「手动」启动，不会随开机自启；
      需要串流时再 on，用完 off 即可。
"""
import subprocess
import sys

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=60)
    return ((p.stdout or '') + (p.stderr or '')).strip()


def service_state():
    out = run('sc query SunshineService')
    running = 'RUNNING' in out.upper()
    cfg = run('sc qc SunshineService')
    start_type = '?'
    for line in cfg.splitlines():
        if 'START_TYPE' in line:
            start_type = line.split(':')[-1].strip()
    return running, start_type


def adb_count():
    try:
        p = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq adb.exe'],
                           capture_output=True, text=True, timeout=30)
        return (p.stdout or '').lower().count('adb.exe')
    except Exception:
        return -1


def do_status():
    running, st = service_state()
    print('Sunshine 服务 : %s（启动类型 %s）' % ('运行中' if running else '已停止', st))
    print('adb 守护进程 : %s 个进程' % adb_count())


def do_on():
    print(run('net start SunshineService') or 'Sunshine 已启动或无需启动')
    do_status()


def do_off():
    print(run('net stop SunshineService') or 'Sunshine 已停止')
    print(run('"%s" kill-server' % ADB) or 'adb 已停止')
    do_status()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    {'on': do_on, 'off': do_off, 'status': do_status}.get(cmd, do_status)()
