# 康佳各平台强制升级方法汇总（原 .doc 提取）

来源：`康佳各种平台强制升级方法汇总.doc`（原文档标题「2013 年主产平台升级方法汇总」）
提取方式：从 OLE2 复合文档的 `WordDocument` 流中按 UTF-16LE 还原表格文本（本机未装 Office/LibreOffice）

---

## 原表

| 主芯片型号 | Mboot 强制升级方法 | Mboot 升级文件名称 | 主程序强制升级方法 | 主程序升级文件名称 | 备注 |
|---|---|---|---|---|---|
| MSD6A918 | 遥控器的 **音量减** | mboot.bin | 遥控器 **音量加** | **MstarUpgrade.bin** | 安卓系统 |
| MSD6A818 | 遥控器的 **音量减** | mboot.bin | 遥控器 **音量加** | **MstarUpgrade.bin** | 安卓系统 |
| RTD2995 | 和主程序合一 | — | 电视机 VOL+ 键（音量加键） | Install.img | 安卓系统 |
| RTD2992 | 和主程序合一 | — | 电视机 VOL+ 键（音量加键） | Install.img | 安卓系统 |
| MSD6A901 | 遥控器或电视机的 **音量减** | mboot.bin | 遥控器或电视机的 **待机** | **MstarUpgrade.bin** | 安卓系统 |
| MSD6A800 | 遥控器的 **音量减** | mboot.bin | 遥控器的 **待机** | **MstarUpgrade.bin** | 安卓系统 |
| MSD6A801 | 遥控器的 **音量减** | mboot.bin | 遥控器的 **待机** | **MstarUpgrade.bin** | 安卓系统 |
| MSD6A981J | 按压电视机上的 **待机** | Target 文件夹 | （短路 N507 的 5、6 脚） | Target 文件夹 | OMI 系统 |
| MSD6A981J（6i78） | 短路 N507 的 5、6 脚 | Target 文件夹 | — | Target 文件夹 | OMI 系统 |
| MSD6A981J（6i98） | 按压电视机上的 **待机** | Target 文件夹 | — | Target 文件夹 | OMI 系统 |
| MT8227 | — | MTKDTV.BIN | — | — | 非智能电视 |
| RTD2649 | 按键板的 **menu 键** | Install.img | — | — | 网络电视 |
| RTD2985DQ | 使用电脑强制升级 | dvrboot.rescue.exe.bin | 电视机 VOL+ 键（音量加键） | Install.img | 安卓系统 |

**官方关于松手时机的表述**
- Mboot：「按压某个键开机，**看到指示灯闪烁后**松开」
- 主程序：「按压某个键开机，**看到指示灯闪烁或有升级界面后**松开」

---

## 对本机（KKTV AK50，MSD648 / mstar6a648）的推论

**MSD648 不在本表内**（该表覆盖的是 2013 年主产平台，648 属于后续平台）。
但 MStar 全系的命名与按键规律高度一致，可直接套用：

1. **主程序文件名 = `MstarUpgrade.bin`，且必须解压后放入 U 盘根目录**
   —— 这是本表最重要的信息。维修论坛流传的「zip 不要解压」是**海思平台**的做法
   （对应 `HV55*Upgrade.zip`），套到 MStar 上会导致电视根本识别不到固件。
2. **主程序触发键有两个候选**：6A918/6A818 派用**音量加**，6A901/6A800/6A801 派用**待机键**。
   648 无法直接判定 → **先试音量加，不触发立刻改试待机键**。
3. **mboot 一律走音量减**，且刷的是 `mboot.bin`。
   本机每次都能开机、能进到 KKTV LOGO、音量键有反应 → **mboot 完好，不要刷 mboot.bin**。
4. MStar 平台主程序文件名统一，因此选包时可用文件名反查平台：
   出现 `MstarUpgrade.bin` / `M648Upgrade.bin` → MStar ✅；
   出现 `HV55*Upgrade.zip` → 海思 ❌（刷入必砖）。
