# 脚本清单

使用前**必须改**的两个路径常量（在每个 `.py` 顶部）：

```python
ADB  = r"C:\...\platform-tools\adb.exe"    # 改成你的 adb
AAPT = r"F:\AK50\05_工具\aapt.exe"         # godmode.py 需要，用于解析 APK manifest
```

默认连的是 `192.168.50.52:5555`（盒子）；电视是 `192.168.50.17`。
git-bash 下先 `export MSYS_NO_PATHCONV=1`。

---

## 这次的主角

| 脚本 | 干什么 |
|---|---|
| **`godmode.py`** | **"上帝模式"组件管理器**。`list` 列全部组件 + 状态 / `ad` 看广告类候选 / `state` 看禁用清单 / `disable` `enable` 组件 / `launch` 直达任意 Activity。详见 [docs/04](../docs/04-上帝模式组件裁剪.md) |

## 拿 root 与命令通道

| 脚本 | 干什么 |
|---|---|
| `rc_client.py` | StbTool HTTP 服务的客户端（`cmd` 远程 shell、`dl` 下载等） |
| `rc4.py` / `rc_batch.py` | 批量命令 / 恢复通道兜底 |
| `serve_once.py` | 一次性 HTTP 文件服务（配合盒子上的 `nc` 免 U 盘传文件） |
| `up.py` | POST 上传文件到盒子（命令通道挂了时的兜底） |
| `adbX.py` | adb 包装（daemon 被回收时自动重连） |

## 直播源

| 脚本 | 干什么 |
|---|---|
| `probe_union.py` | 117 个频道全量 302 探测 → `union_map.json` |
| `gen_live_m3u.py` | 生成 IPTV m3u（凭据从抓包文件读取，不硬编码） |
| `apply_groups.py` | 给 m3u 加中文名 + `group-title` 分组 |
| `push_live.py` | 把生成的源推到设备 |
| `pcap_*.py` / `probe_union.py` | 抓包响应的解析辅助 |

## 桌面 / 应用

| 脚本 | 干什么 |
|---|---|
| `build_only.py` | 只编译，产出 APK |
| `build_install.py` | 编译 + 安装 |
| `final_deploy.py` | 部署桌面到盒子（含开无障碍） |
| `deploy_box_desktop.py` | 同上（早期版） |
| `freeze_safe.py` | 安全冻结（带白名单保护，避免冻坏桌面） |
| `test_sendevent_menu.py` / `test_loop.py` | 菜单键切换闭环测试（用 `sendevent`，不用 `input`） |
| `acc_check.py` / `acc_diag.py` | 无障碍服务状态诊断 |
| `tv_wifi.py` | 给设备配 WiFi（`scan` / `connect <ssid> <pwd>` / `status`，走 wpa_cli） |

## 侦察

| 脚本 | 干什么 |
|---|---|
| `fullscan.py` / `adb_probe.py` / `probe_box.py` | 端口与信息探测 |
| `digest7546.py` | 验证 7546 的 Digest 认证是空壳（168 组账密全 200） |
| `probe7546.py` / `probe2.py` / `probe3.py` / `probe4.py` | 各端口试探 |
| `gm_login.py` | 光猫（GM220-S）RSA 登录 |
| `ls_prefs.py` | 列出应用 SharedPreferences |

## 其它

| 脚本 | 干什么 |
|---|---|
| `build_repo.py` | **本仓库的生成脚本**：复制工程 + 自动脱敏（手机号 / MAC / STBID / IPv6 / 真实直播地址） |
| `mkicon.py` / `push_wallpapers.py` | 桌面图标、壁纸 |
| `cleanup_dialog.py` | 清理残留对话框 |

> 所有脚本都按"本机环境"写的，换机器基本都要改 IP 和路径常量，别指望开箱即用 —— 把它们当成**可复用的思路和命令模板**看更合适。
