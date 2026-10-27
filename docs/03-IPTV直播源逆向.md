# 03 · IPTV 直播源逆向（江苏移动 / GITV）

结论先说：**这台盒子的 IPTV 直播流，普通宽带（公网）也能播** —— 不需要把盒子接到光猫的 iTV 口。
（此前"移动内网源必须走 IPTV 专网"的结论，只对 `223.110.245.x` 那组地址成立。）

---

## 1. 三段式链路（抓包得到）

```
① dispatcher
   jscmcc-livod.dispatcher.gitv.tv  /gitv_live/<chnCode>/<chnCode>.m3u8?...token...
   → 返回 {"url": "<模板>/gitv/live1/<chnCode>/<chnCode>"}（模板里的 %s 直接去掉）

② 入口（江苏移动）
   183.207.249.71  GET <模板路径>?UserName=<手机号>&MAC=<盒子MAC>&OTTUserToken=<...>&accountinfo=<...>
   → 302

③ 最终 CDN
   http://ott.mobaibox.com/PLTV/<3或4>/224/<频道ID>/index.m3u8?<同一套 auth>
   → 解析到 223.110.242.x（公网可达 ✅）
```

关键点：

- **`accountinfo` 是账号级的，全频道通用** —— 不用一个频道抓一次。
- 最终用**域名** `ott.mobaibox.com` 而不是写死 IP，让它自动调度到就近 CDN 节点。
- `223.110.242.x` 普通宽带公网可达；`223.110.245.x` / `ott.js.chinamobile.com` 才在 IPTV 专网里，公网完全超时。
- 鉴权会过期，过期后重跑 `gen_live_m3u.py` 即可。

## 2. 抓包怎么做的

盒子上有 `/system/xbin/tcpdump`（root 后直接跑）：

```bash
/system/xbin/tcpdump -i eth0 -s0 -w /mnt/sdcard/x.pcap 'port 53 or port 80' &
# 然后遥控器切到直播、换几个台
adb pull /mnt/sdcard/x.pcap .
```

注意：盒子 shell 没有 `pkill`，结束抓包要用 `kill $(grep 出来的 pid)` 或者直接限制包数。

抓包产物里有用的是这几个（都落在 `06_系统快照/盒子/cap/`，**本仓库未收录，含个人鉴权**）：

| 文件 | 用途 |
|---|---|
| `m3u8_url.txt` | 一条完整播放 URL → 从 query 里提取 `UserName` `MAC` `OTTUserToken` `accountinfo` |
| `disp_path.txt` | dispatcher 的完整 path 模板 |
| `chnssl.json` | 117 个 `chnCode`（频道代码） |
| `Channels.db` | `ChannelsTable` 里 176 个中文频道名（用于给频道起名） |
| `EPG_CACHE_DATA.xml` | 少量 alias（只有 9 条，别指望它） |

## 3. 三步生成直播源

```bash
# ① 全量探测：117 个频道逐个跑 302，产出 chnCode ↔ PLTV id 的映射
python scripts/probe_union.py            # → union_map.json

# ② 生成 m3u（默认写到 07_直播源/js_cmcc_iptv.m3u）
python scripts/gen_live_m3u.py

# ③ 分组（脚本里内置 117 个频道的中文名 + 分组映射表 M）
python scripts/apply_groups.py
```

分组结果（写进 `group-title`，播放器里左右键可换组）：
`央视` / `卫视` / `体育` / `影视·剧场` / `纪实·纪录` / `少儿·教育` / `生活·其他` / `江苏·本地` / `公网·备用`

最后把 117 个移动频道和 46 个公网源合并 → **163 频道**，实测在电视上正常播放。

## 4. 播放器

`app/AK直播`（`app.orchard.livetv`）是自写的：

- 频道列表内置在 `assets/live.m3u`（**不依赖 /sdcard**，因为这台设备的 /sdcard 是只读的）；
- 原生支持 `group-title`，左右键换分组；
- 判断有没有真的出画面：`logcat -d | grep -c '\[vo\]'`，有 `[vo] ck_keep, pts:...` 就是视频输出在跑；只有 `write_data buffering... is_data_enough:0` 说明卡在缓冲。

仓库里的 `live.m3u` 是**脱敏模板**（真实地址含账号级 token，不上传），请按上面步骤自己生成。

## 5. 别再试的死路

- **IPv6 源**：家里宽带其实**有** IPv6（电视 eth0 拿到了 `2409:8a20:.../64`，ping6 `2400:3200::1` 只要 18ms），但
  ① fanmingming 那份 ipv6.m3u 的 55 个台全是**北京移动** `[2409:8087:8:21::18]:6610`，跨省一律 **HTTP 400**（连根路径 `/` 都 400，是平台层拒绝，加 UA/Referer 都没用）；
  ② 江苏移动 IPTV 只在专网里。
- **第三方直播壳**（FongMi / TVBox 系 / 当贝 / 喵看）：它们的配置都要写 `/sdcard`，而这台设备 `/sdcard` 只读，装了也用不了。
- 查 IPv6 要用 `busybox ifconfig` 看有没有 `Scope:Global`，别只看 `/proc/net/if_inet6`（容易看漏）。
