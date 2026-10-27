# 02 · FactoryTest 后门拿 root + ADB 持久化

这是整个项目最关键的一步：**在没有 USB 调试开关、遥控器没有数字键、社区秘技（版本号连点 / 472635 / 782782323 / F2F3 / 其他设置连按右键）全部无效的情况下，拿到 root shell。**

---

## 1. 侦察阶段确认过的事实

- 开放端口：`1566 / 2010 / 4008 / 6666 / 7000 / 7546 / 8080 / 8733`，**5555 关闭**，全端口连不上 adb。
- `7546` 的 Digest 认证是空壳：168 组账密全部返回 200 且无内容（`scripts/digest7546.py` 验证过）。
- `4008` 是海思私有升级协议，任何请求一律 400。
- **盒子可以装 APK**：文件管理 → 打开 apk 就能装，并且用户此前用 U 盘装过哔哩哔哩电视版且能正常使用 —— 说明盒子**不拦第三方应用运行**。
- 社区流传的"开 ADB"手法在这台机器上一个都不灵，UI 里的「故障排查 → ADB 状态：打开 / 端口 5555」是假的，改了也不监听。

## 2. 突破口：装一个自己的 APK

思路反转：既然能装 APK，那就让 APK 自己把 shell 开出来。

`app/StbTool2` 干的事：

1. 起一个 HTTP 服务（`:9999`），提供 `/cmd`（执行 shell 命令并回传 stdout）、`/dl`（下载文件）、`/log` `/props` `/mounts` `/pkg` `/ls` `/sig` 等接口；
2. 内置 **factory_test 通道**：执行 `/system/bin/factory_test run_cmd "<命令>"`；
3. `BootReceiver` 开机自启；
4. `mKeepAdb`：开机 8 秒 + 每 60 秒用 factory_test 补拉一次 adbd。

电脑侧客户端：`scripts/rc_client.py`。

```bash
python scripts/rc_client.py cmd "id"
# uid=10031(u0_a31)  ← 普通应用权限

python scripts/rc_client.py cmd "/system/bin/factory_test run_cmd 'id'"
# uid=0(root)        ← 后门生效
```

## 3. 为什么 factory_test 能提权

`/system/bin/factory_test` 是 root 守护进程 **cmccfactory** 的客户端，**完全不校验调用者身份**：
任何 uid 调用它，它都把命令交给 root 守护执行并把 stdout 回传。

于是：

```bash
/system/bin/factory_test run_cmd "setprop service.adb.tcp.port 5555"
/system/bin/factory_test run_cmd "setprop ctl.start adbd"
```

之后：

```bash
adb connect 192.168.50.52:5555
adb shell id    # uid=0(root)  context=kernel
```

`ro.secure=0`，所以 adbd 一起来就是 root，不需要 `adb root`、不需要 su 授权弹窗。

### 这个后门的两个限制

- **只回传 stdout**：`pm` / `dumpsys` 这类"自己 fork 子进程"的脚本命令走这个通道只会回一个 `OK`，拿不到输出。这类命令一律走 adb。
- 它是**本机 root 权限**，不是拿运营商服务器权限，别想多了。

## 4. ADB 为什么会掉（以及怎么修）

现象：手动拉起 adbd 后过一会儿就没了；盒子自带的 ADB 开关怎么点都不生效。

根因：framework 启动完成后会把 `sys.usb.config` 重置为 `none`，init 的属性触发器随即执行 `stop adbd`。

三步修好：

1. **build.prop 追加**（先 `cp /system/build.prop /system/build.prop.orig`）：
   ```
   service.adb.tcp.port=5555
   persist.service.adb.enable=1
   persist.sys.usb.config=adb
   ```
2. **StbTool2 的 mKeepAdb**：`BootReceiver` 开机 8 秒后、以及每 60 秒，用 factory_test 再拉一次 adbd，把 framework 的 stop 抵消掉。
3. 重启验证：断电重启后 5555 与 9998 自动 OPEN，`adb connect` 直连即 `uid=0`。

## 5. 免 U 盘传文件

盒子自带 `/system/xbin/nc`：

```bash
# 电脑
python scripts/serve_once.py 18888 某个文件
# 盒子（用 StbTool / 任意 shell）
/system/xbin/nc 192.168.50.213 18888 > /mnt/sdcard/x.apk
```

然后在盒子「文件管理 → 内部存储」点一下即可安装。

目录权限实测：
- `/mnt/sdcard` 可写但 `noexec`
- `/data/local` 可写**且可执行**（上传二进制用这里）
- `/data/local/tmp` **不可写**

## 6. 装 APK 的注意

- 一键脚本：`scripts/build_install.py`（默认编直播；桌面用 `build_install.py "F:\AK50\03_桌面源码\launcher" app.orchard.tv4 AerialTV4.apk`）
- 只编译不安装：`scripts/build_only.py <项目> <输出名>`
- 装完可能 ADB 掉线，用 `scripts/adbX.py` 补装
- 恢复通道兜底：`scripts/up.py`（POST 上传）→ `scripts/rc4.py cmd "factory_test run_cmd 'pm install -r ...'"`

## 7. 编译产出要校验包名

复制工程改造时最容易踩的坑：`app/build.gradle` 的 `namespace` 还写着旧项目的包名，AGP 会用 namespace 展开 manifest 里的 `.MainActivity`，导致入口类指向不存在的类 → 一启动就 ClassNotFoundException 秒退。

编译后必做：

```bash
aapt dump badging 你的.apk | grep -E "^package:|launchable-activity:"
```

两行的包名前缀必须一致。
