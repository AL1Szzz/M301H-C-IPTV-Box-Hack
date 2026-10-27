# AK50 串流（Sunshine）+ 电视直播 配置说明

日期：2026-10-25 23:40　设备：康佳 KKTV AK50（MSD648 / Android 4.4.4 / 192.168.50.104）
电脑：Windows 11（192.168.50.213，RTX 5060，3440x1440@180Hz）

---

## 一、Sunshine 服务端（电脑侧）—— 已配好

本机 `E:\tool\Sunshine`（"杂鱼"集成版，带 VDD 虚拟显示器 / 虚拟声卡 / 服务脚本）。

| 项目 | 状态 |
|---|---|
| 安装路径 | `E:\tool\Sunshine\sunshine.exe` |
| 版本 | 2026.324.103456（winget 源有更新 2026.914.233613，可不升） |
| 服务 | `SunshineService` = **Running / Automatic（开机自启）** |
| 监听端口 | 47984(https-gui) / 47989(http) / 47990(https) / 48010，全部 `0.0.0.0` |
| 防火墙 | 已有 2 条 Inbound Allow 规则（Sunshine），无需再加 |
| 编码器 | h264_nvenc / hevc_nvenc / av1_nvenc 全部就绪（RTX 5060） |
| mDNS 广播 | 已开启，电视能自动发现这台电脑 |
| Web 控制台 | `https://localhost:47990`（本机免认证）；`https://192.168.50.213:47990`（需登录，用户名 `AL1Szzz`） |
| 应用列表 | Desktop、Steam Big Picture、Xbox Game |

已备份：`E:\tool\Sunshine\config\sunshine_state.json.bak_20261025_233423`

## 二、电视端 Moonlight —— 只剩最后一步

已做的：
- 装好 Moonlight（`com.limelight`，F-Droid 版，minSdk 16，支持 Android TV）
- **降参数**：默认 4K/150Mbps 这台 Mali-T720 扛不住，已改为 **1920x1080 / 15000 kbps**
  （`su -c "busybox sed -i ..."` 改 `/data/data/com.limelight/shared_prefs/com.limelight_preferences.xml`）
- **预置配对证书**：把电视的 `client.crt` 直接写进 Sunshine 的 `named_devices`（设备名 `KKTV-AK50`），
  正常情况下点电脑会直接进应用列表，**不再需要输 PIN**
- 电视已停在 Moonlight 的电脑列表界面

**你现在要做的（遥控器，约 10 秒）**：
1. 电视上用**右方向键**进入电脑列表，选中 `AL1SzzzのPC`（192.168.50.213）
2. 按确认 →
   - 若直接出现 `Desktop / Steam Big Picture` 列表 → 配对成功，选 Desktop 即可看到电脑桌面
   - 若电视显示 **4 位数字** → 电脑上已自动弹出 Sunshine 的 PIN 窗口，把 4 位数输进去点确认

**如果 PIN 窗口没弹出 / 需要手动登录**：电脑浏览器开 `https://localhost:47990`
（用户名 `AL1Szzz`，密码是你 5 月装 Sunshine 时设的）。密码忘了告诉我，我用 `--creds` 重置，
配对过的设备不受影响。

### 已知的一个体验问题
电脑是 **3440x1440 带鱼屏**，电视是 16:9 1080p，直接串流画面会被拉伸。
想要 1:1 无黑边：装 Sunshine 自带的虚拟显示器 —— 以管理员运行
`E:\tool\Sunshine\scripts\install-vdd.bat`，然后在 Sunshine 控制台把输出切到虚拟屏（1920x1080）。
不想折腾就先用拉伸，能看。

## 三、电视看电视台（直播）—— 四条路，按推荐度排

### 1. 电视自带 DTMB 数字电视（最正宗，免费，不依赖网络）
遥控器按**信源**键 → 选 **数字电视 / DTV** → 菜单 → 频道管理 → **自动搜台**。
需要一根天线（随便的有源室内天线就行，十几块钱）插到电视的 RF 口。
搜完就能看央视全套 + 本省卫视 + 本市台，画质是标清/高清地面广播。

### 2. 用刚配好的串流（万能解法，什么都能看）
电视打开 Moonlight → 进电脑桌面 → 电脑上打开央视网直播、咪咕、任何视频网站或客户端。
这条路的优点是**不受电视 Android 4.4 的限制**，电脑上能看的电视上都能看。
这也是 Kazumi（要 Android 10+，电视装不了）的正确打开方式：Kazumi 装电脑，串到电视看。

### 3. 电视自带的牌照方正版应用（已帮你解冻）
之前精简冻掉的这几个是电视预装的正规内容源，**现已解冻**（冻结数 34 → 30，桌面图标已刷新出来）：

| 包名 | 内容 |
|---|---|
| `com.cibn.tv` | CIBN 国广东方（云视听，实测能正常启动联网） |
| `com.bestv.mishitong.tv` | 百视通（含部分直播频道） |
| `com.gitvkonka.video` | GITV 银河 |
| `com.konka.mor.tv` | 康佳自带内容应用 |

想再冻回去：`adb shell su -c "pm disable-user --user 0 <包名>"`

### 4. 当贝市场里搜装
电视上打开**当贝市场** → 搜索"直播"/"电视家"/"HDP"等，装完即可。
（我这边的下载源受限，GitHub / APKMirror / F-Droid 官网都不通，所以这类应用你自己装更快。）

### ❌ 装不了的
**央视频TV / CCTV.新视听**：官方要求 **Android 5.0~6.0 以上**，你这台是 4.4，直接被系统拒绝。
老版"央视影音 TV 版"理论上可能兼容，但我这边下不到可靠的官方直链，没有强推。

---

## 附：本次用到的关键命令

```bash
# 启动/停止 Sunshine 服务
net start SunshineService
net stop  SunshineService

# 电视端 root 命令（SuperSU 已授权，su 直接可用）
adb shell su -c "pm enable com.cibn.tv"
adb shell su -c "pm list packages -d"

# 改串流参数（电视上没有 sed，必须用 busybox）
adb shell su -c "busybox sed -i 's/3840x2160/1920x1080/g' \
  /data/data/com.limelight/shared_prefs/com.limelight_preferences.xml"
```
