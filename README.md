# M301H-C 江苏移动 IPTV 盒子 · 改造笔记（含 root / 直播源 / 组件裁剪 / 自建桌面）

给**同型号、同运营商定制机**的一份完整作业。所有步骤都在真机上跑通并验证过，不是纸上推演。

---

## 一、先确认你的机器对不对

| 项目 | 本机实测值 |
|---|---|
| 型号 | **M301H-C**（Skyworth/创维代工，江苏移动定制） |
| 芯片 | 海思 **Hi3798MV310** |
| 系统 | Android **4.4.2**，内核 `3.18.24_hi3798mv310` |
| 软件版本 | V.798.05 |
| 桌面 | GITV 江苏移动专版 `com.gitv.launcher` 5.2.52 |
| 网卡 | 有线 eth0 + 无线 wlan0（都有网） |

**判断你的机器能不能复现本项目的 root 后门**，只要一条：

```bash
ls -l /system/bin/factory_test
```

存在这个文件，且它是 `cmccfactory` 守护进程的客户端 → 后门可用（详见 [docs/02](docs/02-FactoryTest后门与ADB持久化.md)）。
另外 UPnP 端口 1566 会自报 `friendlyName: M301H-C`、`manufacturerURL: mobee.tv`。

---

## 二、这套作业能拿到什么

| # | 成果 | 关键点 |
|---|---|---|
| 1 | **root shell**（无需 U 盘、无需开 ADB 调试） | `/system/bin/factory_test run_cmd` 后门 |
| 2 | **ADB 重启后自动在线** | build.prop + 开机自拉 adbd |
| 3 | **163 个频道的 IPTV 直播源** | 移动内网源经 dispatcher 后落到**公网可达** CDN，普通宽带能播 |
| 4 | **"上帝模式"组件裁剪**（禁了 11 个） | 广告屏保 / 升级弹窗 / 静默安装 / 支付页 全掐掉 |
| 5 | **自建桌面 AerialTV4 + 双桌面切换** | HOME 回官方桌面，菜单键切出自建桌面 |

---

## 三、抄作业顺序（建议严格按这个来）

### 0. 准备
- 一台能装 APK 的盒子（**这台盒子不拦第三方应用**：文件管理 → 打开 apk 即可安装）
- 电脑装好 adb；脚本里的 `ADB` / `AAPT` 路径常量需要改成你本机的（见 [scripts/README](scripts/README.md)）
- git-bash 下跑脚本前先 `export MSYS_NO_PATHCONV=1`（否则 `/status` 这类参数会被当成路径转换掉）

### 1. 打通命令通道（还没 root 时）
装 `app/StbTool2`（内置 HTTP 服务，9999 端口），它能在**普通应用权限**下给你一个远程 shell：

```bash
python scripts/rc_client.py cmd "id"        # 返回 uid=100xx（app 权限）
python scripts/rc_client.py cmd "/system/bin/factory_test run_cmd 'id'"   # 返回 uid=0(root)
```

### 2. 拿到 root
`factory_test` 是 root 守护 `cmccfactory` 的客户端，**不校验调用者**，谁调都是 root 执行：

```bash
# 起 adbd
/system/bin/factory_test run_cmd "setprop service.adb.tcp.port 5555"
/system/bin/factory_test run_cmd "setprop ctl.start adbd"
```
然后 `adb connect 192.168.50.52:5555` → 直接就是 `uid=0(root)`（`ro.secure=0`）。
**注意**：`pm` / `dumpsys` 这类脚本命令走这个通道只会回 `OK`，拿不到输出；这类命令要走 adb。

### 3. ADB 持久化
不处理的话，framework 起来后会把 `sys.usb.config` 重置成 `none`，init 随即 `stop adbd`（这就是"盒子自带 ADB 开关无效"的真相）：
- `build.prop` 追加 `service.adb.tcp.port=5555`（**先备份 build.prop**）
- StbTool2 的 `mKeepAdb`：开机 8 秒 + 每 60 秒用 factory_test 补拉一次 adbd

重启验证：`adb connect` 直接是 root。

### 4.（可选）直播源
见 [docs/03](docs/03-IPTV直播源逆向.md)。一句话原理：
dispatcher → 入口 302 → `ott.mobaibox.com/PLTV/.../index.m3u8`，**accountinfo 是账号级的、全频道通用**，最终 CDN `223.110.242.x` 在**普通宽带公网可达**（同网段 `223.110.245.x` 才需要 IPTV 专网）。

### 5.（可选）组件裁剪（"上帝模式"）
见 [docs/04](docs/04-上帝模式组件裁剪.md)。最常用的一条：

```bash
python scripts/godmode.py list com.gitv.launcher      # 列出全部组件 + 启用状态
python scripts/godmode.py ad   com.gitv.launcher      # 只看广告/推送/统计类候选
python scripts/godmode.py disable com.gitv.launcher .ui.NewAdScreenSaverActivity
```

### 6.（可选）自建桌面
见 [docs/05](docs/05-自建桌面与双桌面切换.md)。

---

## 四、目录说明

```
scripts/          所有 Python 工具（godmode.py 是这次的主角）
app/AerialTV4/    自建电视桌面（极简、支持冻结管理、菜单键切换）
app/AK直播/       自写直播播放器（原生支持 group-title 分组）
app/StbTool2/     盒子上跑的远程助手（HTTP 服务 + 拉起 adbd）
app/StbHello/     最小验证 APK（判断第三方应用能不能跑）
docs/             分步骤教程
docs/legacy/      早期针对康佳 AK50 电视的笔记（同一项目的另一半）
```

---

## 五、踩坑速查（血泪版）

完整版在 [docs/06](docs/06-踩坑清单.md)，最容易中招的几条：

1. **别冻结这 5 个应用**：`jshdc.appstore`（桌面"应用中心"本体）、`appusage`、`personalcenter`、`msg.agent`、`sdk.upgrade` —— 桌面强依赖，冻了"我的应用"就一直转圈。要裁就**用组件级禁用**，别冻整个应用。
2. **`pm install -r` 覆盖装 StbTool2 会杀掉服务且不自启** → 命令通道没了。要么遥控器手动打开一次，要么断电重启。
3. **`input keyevent` 不经过无障碍过滤层** → 调试菜单键拦截必须用 `sendevent /dev/input/event0 1 139`（Linux 扫描码 139 = KEYCODE_MENU）。
4. **`adb pull` 不认中文路径**（Illegal byte sequence）→ 用英文目录。
5. **复制 Android 工程改造时，`namespace` / `applicationId` / manifest package / 源码目录必须一起改**。否则 AGP 会用旧 namespace 展开 `.MainActivity`，装上去直接 ClassNotFoundException 秒退。
6. **DirtyCOW 在这台机器上已修补**（内核 2018-03 编译），别浪费时间。
7. **盒子 shell 没有 `printf` / `tail` / `sed` / `head` / `pkill` / `pidof`**，写脚本时别用。

---

## 六、已知边界（别再浪费时间）

- **顶部栏目（音乐/教育/苏超/Bilibili…）改不掉**：那是服务端下发的 JS 模板渲染的，不是 Android 组件，`pm disable` 够不着；改本地缓存无效（启动时实时拉取）；hosts 屏蔽配置域名也无效（App 内置硬编码 IP 兜底）。
- **官方"导航管理"页面按 OK 会提示"您暂时不能管理该频道"**：`isShowNavigationManage` 和每个栏目的可管理标记都由服务端下发，本地改不动。
- iptv 直播流本身**不需要** IPTV 专网（前提是拿到 accountinfo），但 accountinfo 会过期，过期后重跑 `gen_live_m3u.py`。

---

## 七、免责

本仓库仅为**自用设备改造与学习**的记录整理。请勿用于绕过他人设备的访问控制、传播运营商直播源或任何商业用途；操作前请自行备份分区（本项目备份了 14 个分区镜像）。因参照本仓库操作造成的任何损失，作者不承担责任。
