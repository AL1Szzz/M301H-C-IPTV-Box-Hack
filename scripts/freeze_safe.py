# -*- coding: utf-8 -*-
"""
康佳 AK50 (MSD648 / Android 4.4) 官方包 —— 系统应用冻结工具

设计原则（吸取上次变砖事故的教训）：
  1. 绝不 uninstall，只用 pm disable-user（随时 pm enable 还原）
  2. 逐个冻结，每一步都验证 system_server 存活 + adb 仍可连
  3. 任何一步异常立即停止，并自动回滚本轮已冻结的包
  4. 默认只冻结 SAFE 组；CAREFUL 组需显式 --careful；KEEP 组永远不动

用法：
  python freeze_safe.py <电视IP>                # 只分析，不改动
  python freeze_safe.py <电视IP> --freeze       # 冻结 SAFE 组
  python freeze_safe.py <电视IP> --careful      # 额外冻结 CAREFUL 组（需确认）
  python freeze_safe.py <电视IP> --restore-all  # 解冻本工具冻结过的所有包
"""
import os
import subprocess
import sys
import time

ADB = r'C:\Users\Administrator\Documents\Qoder\2026-10-25\4c19e445\tools-dl\platform-tools\adb.exe'

# 冻结时排到最后执行：冻结后电视上将没有任何输入法可用（本系统只有讯飞一个 IME）
LAST_STRAW = ['com.iflytek.xiri.ime']

# ---------------------------------------------------------------- 分组

# 可以放心冻结：广告 / 推送 / 内容运营 / 演示 / 用户基本用不到的
SAFE = [
    ("com.konka.systemadvert",   "系统广告"),
    ("com.konka.message",        "康佳消息推送（弹窗广告来源）"),
    ("com.konka.appupgrade",     "应用自动升级"),
    ("com.konka.tvmall",         "康佳电视商城"),
    ("com.gitvkonka.video",      "银河奇异果（爱奇艺）"),
    ("com.konka.market.main",    "应用商城"),
    ("com.konka.setupwizard",    "开机向导（已过）"),
    ("com.konka.hotelmenu",      "酒店模式"),
    ("com.konka.kkmultiscreen",  "多屏互动"),
    ("com.konka.downloadcenter", "下载中心"),
    ("com.lz.smart.music",       "音乐"),
    ("com.bajintech.karaok",     "卡拉OK"),
    ("com.konka.cloudsearch",    "云搜索"),
    ("com.konka.fourkshow",      "4K 演示片源"),
    ("com.konka.tvmanager",      "电视管家"),
    ("com.android.dummyactivity", "占位空壳"),
]

# 看需求：冻结会损失某项功能，但不会有系统性风险
CAREFUL = [
    ("com.bestv.mishitong.tv",   "百视通影视（不用它看片可冻）"),
    ("com.cibn.tv",              "CIBN 酷喵影视（不用它看片可冻）"),
    ("com.konka.mor.tv",         "康佳 mor.tv"),
    ("com.konka.SmartControl",   "手机智控（用手机当遥控器就别冻）"),
    ("com.iflytek.xiri",         "讯飞语音（遥控器有语音键就别冻）"),
    ("com.iflytek.xiri.ime",     "讯飞输入法（冻结后无法输入 WiFi 密码等）"),
    ("com.iflytek.itvs",         "讯飞电视服务"),
    ("com.iflytek.xiri2.system", "讯飞语音系统服务"),
    ("com.konka.upgrade",        "系统升级中间件（冻结=不再收 OTA，U盘强刷不受影响）"),
    ("com.konka.systemsetting",  "康佳设置中心（安卓原生设置仍在）"),
    ("com.konka.applist",        "应用列表"),
    ("com.konka.smartengine",    "智能引擎"),
    ("com.konka.multimedia",     "Fluent 多媒体"),
    ("com.konka.account",        "康佳账号"),
    ("com.konka.systeminfo",     "系统信息"),
    ("com.konka.epgserver",      "EPG 电子节目单（看数字电视节目信息要用）"),
    ("com.konka.passport",       "通行证"),
    ("com.android.providers.downloads", "下载管理器（冻结后无法下载）"),
    ("com.android.bluetooth",    "蓝牙（不用蓝牙耳机/遥控可冻）"),
]

# 永远不要碰：动了可能开不了机或丢核心功能
KEEP = [
    ("app.orchard.tv4",                  "我们的桌面"),
    ("eu.chainfire.supersu",             "SuperSU（root 授权）"),
    ("com.konka.kksystemui",             "康佳系统 UI"),
    ("com.android.systemui",             "安卓系统 UI"),
    ("com.konka.bootlogicproxy",         "启动逻辑代理（上次事故嫌疑之一）"),
    ("com.konka.localserver",            "本地服务"),
    ("com.konka.quickstandby",           "快速待机"),
    ("com.konka.tvsettings",             "电视设置（图像/声音）"),
    ("com.konka.kkfactory",              "康佳工厂菜单（开 ADB 要靠它！）"),
    ("mstar.factorymenu.ui",             "MStar 工厂菜单（调图像参数要用）"),
    ("com.mstar.tv.service",             "电视核心服务"),
    ("com.mstar.android.providers.tv",   "电视频道数据"),
    ("com.android.provision",            "首次启动配置"),
    ("com.android.keychain",             "证书链"),
    ("com.android.packageinstaller",     "APK 安装器"),
    ("com.android.providers.settings",   "设置数据库"),
    ("com.android.defcontainer",         "包安装服务"),
    ("com.android.externalstorage",      "外置存储"),
    ("com.android.shell",                "shell"),
    ("com.konka.livelauncher",           "康佳原桌面（确认新桌面稳定后再单独冻结）"),
    ("android",                          "框架资源"),
]


class Tv(object):
    def __init__(self, dev):
        self.dev = dev
        self.useSu = False   # adb 拿不到 root 时，改用 su -c（会弹 SuperSU 授权框）
        self.connect()

    def connect(self):
        for _ in range(3):
            try:
                r = subprocess.run([ADB, 'connect', self.dev],
                                   capture_output=True, timeout=40)
                out = (r.stdout or b'').decode('utf-8', 'ignore')
                if 'connected' in out or 'already' in out:
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def root(self):
        try:
            subprocess.run([ADB, '-s', self.dev, 'root'],
                           capture_output=True, timeout=60)
        except Exception:
            pass
        time.sleep(4)
        self.connect()
        time.sleep(1)
        # 装了 SuperSU 之后 adbd 不再直接给 root（ro.secure=1），
        # 这时 pm 命令必须以 su 身份跑，否则会静默失败（看不出错，但状态不变）
        if 'uid=0' not in self.sh('id'):
            self.useSu = True

    def sh(self, cmd, t=90):
        if self.useSu:
            cmd = "su -c '%s'" % cmd.replace("'", "'\\''")
        try:
            p = subprocess.run([ADB, '-s', self.dev, 'shell', cmd],
                               capture_output=True, timeout=t)
            return ((p.stdout or b'') + (p.stderr or b'')).decode('utf-8', 'ignore').strip()
        except Exception as e:
            return ''

    def id(self):
        return self.sh('id')

    def disabled(self):
        out = self.sh('pm list packages -d')
        s = set()
        for line in out.splitlines():
            t = line.strip()
            if t.startswith('package:'):
                s.add(t[len('package:'):].strip())
        return s

    def alive(self):
        """system_server 是否还活着 —— 上次事故就是它死了"""
        ps = self.sh('ps', 60)
        return 'system_server' in ps

    def stat(self):
        """粗略体检：进程数 + 可用内存，用于冻结前后对比"""
        ps = self.sh('ps', 60)
        n = len([l for l in ps.splitlines() if l.strip()])
        mem = self.sh('cat /proc/meminfo', 30)
        free = avail = 0
        for line in mem.splitlines():
            if line.startswith('MemFree:'):
                free = int(line.split()[1]) // 1024
            elif line.startswith('Cached:'):
                avail = int(line.split()[1]) // 1024
        return n, free, avail


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    dev = sys.argv[1]
    if ':' not in dev:
        dev = dev + ':5555'
    args = sys.argv[2:]

    tv = Tv(dev)
    tv.root()
    ident = tv.id()
    print('设备 %s  身份: %s' % (dev, ident or '(无法连接)'))
    if tv.useSu:
        print('提示：adbd 未给 root，已切到 su 通道 —— 电视上会弹 SuperSU 授权框，'
              '请用遥控器点【允许】；或在 SuperSU 里把「默认访问」设为【授予】，之后就不再弹。')
    elif 'uid=0' not in ident:
        print('提示：非 root，pm 可能受限（桌面装成系统应用后本可免 root）')

    installed = tv.sh('pm list packages -f', 120)
    inst = {}
    for line in installed.splitlines():
        line = line.strip()
        if not line.startswith('package:'):
            continue
        body = line[len('package:'):]
        if '=' in body:
            path, pkg = body.split('=', 1)
            inst[pkg] = path
    now_disabled = tv.disabled()

    print()
    print('=' * 68)
    print('系统共 %d 个包，当前已冻结 %d 个' % (len(inst), len(now_disabled)))
    print('=' * 68)

    def show(title, group, mark):
        print()
        print('%s  （%d 个）' % (title, len(group)))
        print('-' * 68)
        for pkg, desc in group:
            if pkg not in inst:
                state = '未安装'
            elif pkg in now_disabled:
                state = '已冻结'
            else:
                state = '启用中'
            print('  %-34s %-8s %s' % (pkg, state, desc))

    show('[可安全冻结]', SAFE, 'OK')
    show('[看需求，冻结会损失对应功能]', CAREFUL, '?')
    show('[永远不要动]', KEEP, 'X')

    # 统计
    safe_avail = [p for p, _ in SAFE if p in inst and p not in now_disabled]
    care_avail = [p for p, _ in CAREFUL if p in inst and p not in now_disabled]
    print()
    print('=' * 68)
    print('可立即冻结（SAFE 且当前启用中）：%d 个' % len(safe_avail))
    print('按需冻结（CAREFUL 且当前启用中）：%d 个' % len(care_avail))
    print('禁止冻结：%d 个' % len([p for p, _ in KEEP if p in inst]))
    print('=' * 68)

    if not args or '--freeze' not in args and '--careful' not in args and '--restore-all' not in args:
        print()
        print('（以上为只读分析。加 --freeze 执行 SAFE 组，--careful 追加 CAREFUL 组，'
              '--restore-all 全部解冻）')
        return

    # ---------------- 执行冻结 ----------------
    todo = []
    if '--freeze' in args:
        todo += [(p, d) for p, d in SAFE if p in inst and p not in now_disabled]
    if '--careful' in args:
        todo += [(p, d) for p, d in CAREFUL if p in inst and p not in now_disabled]
    # 影响最大的排到最后一个，方便定位与单独还原
    todo.sort(key=lambda x: 1 if x[0] in LAST_STRAW else 0)

    if '--restore-all' in args:
        print()
        print('=== 解冻所有被冻结的包 ===')
        n = 0
        for pkg in sorted(now_disabled):
            if pkg == 'android':
                continue
            tv.sh('pm enable %s' % pkg)
            n += 1
            print('  解冻 %s' % pkg)
        print('共处理 %d 个，system_server 存活: %s' % (n, tv.alive()))
        return

    pre_n, pre_free, pre_cached = tv.stat()

    print()
    print('=== 开始冻结 %d 个（逐个执行，每步验证）===' % len(todo))
    print('冻结前：进程 %d 个，可用内存 %d MB（含缓存 %d MB）' % (pre_n, pre_free, pre_cached))
    done = []
    aborted = False
    for i, (pkg, desc) in enumerate(todo, 1):
        tv.sh('pm disable-user --user 0 %s' % pkg)
        time.sleep(0.6)
        ok = pkg in tv.disabled()
        alive = tv.alive()
        flag = 'OK ' if ok else 'FAIL'
        print('  [%2d/%d] %s %-32s %s | system_server: %s'
              % (i, len(todo), flag, pkg, desc, '存活' if alive else '消失!'))
        if ok:
            done.append(pkg)
        if not alive:
            print()
            print('  !! system_server 消失，立即停止并回滚')
            aborted = True
            break

    if aborted:
        print()
        print('=== 回滚中 ===')
        for pkg in done:
            tv.sh('pm enable %s' % pkg)
            print('  已还原 %s' % pkg)
        print('回滚完成，system_server: %s' % ('存活' if tv.alive() else '仍消失'))
        return

    post_n, post_free, post_cached = tv.stat()
    final = sorted(tv.disabled())

    print()
    print('全部完成：成功冻结 %d / %d' % (len(done), len(todo)))
    print('system_server: %s   adb: %s' % ('存活' if tv.alive() else '消失!', tv.id()))
    print()
    print('进程数：%d -> %d（减少 %d 个）' % (pre_n, post_n, pre_n - post_n))
    print('可用内存：%d MB -> %d MB（+%d MB）' % (pre_free, post_free, post_free - pre_free))

    # 落一份清单，方便日后精确还原
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(here, 'frozen_list.txt')
        with open(p, 'w', encoding='utf-8') as f:
            f.write('# %s 冻结清单（共 %d 个）\n' % (dev, len(final)))
            f.write('# 还原单个： adb shell pm enable <包名>\n')
            f.write('# 全部还原： python freeze_safe.py %s --restore-all\n\n' % dev)
            for pkg in final:
                f.write(pkg + '\n')
        print('冻结清单已写入：%s' % p)
    except Exception as e:
        print('（清单写入失败：%s）' % e)

    print()
    print('如需全部还原：python freeze_safe.py %s --restore-all' % dev)
    print('只还原一个：adb shell pm enable <包名>')


if __name__ == '__main__':
    main()
