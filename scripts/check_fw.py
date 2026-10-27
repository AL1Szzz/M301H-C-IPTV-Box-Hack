"""
康佳 AK50 (MSD648) 固件包刷前校验工具
用法（用下面的 python 路径）：
    python check_fw.py D:\\              # 扫描 U 盘根目录
    python check_fw.py D:\\MstarUpgrade.bin
    python check_fw.py C:\\Users\\...\\Downloads\\xxx.zip

作用：
  1. 列出文件（名/大小）
  2. 抽取文件头部的可打印字符串，判断平台归属
  3. 对"海思 hisiv553"包给出红色拦截警告 —— 那是唯一会真砖的情况
"""
import os
import re
import sys

HISI_KEYS = ["hv55", "hisilicon", "hisi", "hi3798", "hi3751", "dvrboot", "rescue"]
MSTAR_KEYS = ["mstar", "mst", "msd6", "6a648", "mboot", "mstarupgrade", "m648"]
INSTALL_KEYS = ["install.img", "installimage"]


def dump_strings(path, limit=8192):
    with open(path, "rb") as f:
        head = f.read(limit)
    ascii_pat = re.compile(rb"[\x20-\x7e]{4,}")
    out = []
    for m in ascii_pat.finditer(head):
        out.append(("ascii", m.group().decode("ascii", "ignore")))
    try:
        u16 = head.decode("utf-16-le", errors="ignore")
        for m in re.finditer(r"[\x20-\x7e]{4,}", u16):
            out.append(("u16", m.group()))
    except Exception:
        pass
    return out


def looks_zip(path):
    with open(path, "rb") as f:
        return f.read(4) == b"PK\x03\x04"


def verdict(name, strings):
    blob = " ".join([s[1] for s in strings]).lower()
    name_l = name.lower()
    hits_hisi = [k for k in HISI_KEYS if k in blob or k in name_l]
    hits_mstar = [k for k in MSTAR_KEYS if k in blob or k in name_l]
    return hits_hisi, hits_mstar


def scan_file(path):
    size = os.path.getsize(path)
    print("\n" + "=" * 68)
    print("文件: %s" % path)
    print("大小: %.2f MB (%d bytes)" % (size / 1024 / 1024, size))
    is_zip = looks_zip(path)
    print("格式: %s" % ("ZIP 压缩包 → 需解压后再放进 U 盘" if is_zip else "非 ZIP（可能是裸镜像）"))

    if size < 1024 * 1024:
        print("!! 体积过小（<1MB），不像是完整的主程序包，确认下是否下载完整")
        return

    strings = dump_strings(path)
    if not strings:
        print("头部无可读字符串（二进制镜像，正常）")
        return

    print("---- 头部字符串（前 24 条）----")
    for kind, s in strings[:24]:
        print("  [%s] %s" % (kind, s))

    hits_hisi, hits_mstar = verdict(os.path.basename(path), strings)
    print("---- 判定 ----")
    if hits_hisi:
        print("### 危险：检测到海思特征 %s" % hits_hisi)
        print("### 这是 hisiv553 平台的包，刷进 MSD648 会真砖。立即停用这个包。")
    elif hits_mstar:
        print("OK 检测到 MStar 特征 %s → 与本机 MSD648 平台一致，可以刷" % hits_mstar)
    else:
        print("?? 未识别出平台特征，请看上面的头部字符串人工确认")
    if is_zip:
        print("提示: MSD648 平台要解压出 M648Upgrade.bin 再放 U 盘根目录（不要改名成 MstarUpgrade.bin）")


def scan_dir(root):
    print("扫描目录: %s" % root)
    entries = []
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            entries.append(p)
    if not entries:
        print("目录里没有任何文件 —— U 盘是空的？")
        return
    entries.sort(key=lambda p: -os.path.getsize(p))
    for p in entries:
        try:
            scan_file(p)
        except Exception as e:
            print("\n[跳过] %s (%s)" % (p, e))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("请给出 U 盘盘符或固件文件路径，例如: python check_fw.py D:\\")
        return
    target = sys.argv[1]
    if os.path.isdir(target):
        scan_dir(target)
    elif os.path.isfile(target):
        scan_file(target)
    else:
        print("路径不存在: %s" % target)
    print("\n" + "=" * 68)
    print("刷前自检清单:")
    print("  1. U 盘是 FAT32 格式（不是 NTFS/exFAT）")
    print("  2. 根目录只有固件文件，没有子文件夹、没有照片视频")
    print("  3. MStar 平台：放的是解压后的 MstarUpgrade.bin，不是 zip")
    print("  4. U 盘插在黑色 USB 2.0 口（蓝色 3.0 口不认）")


if __name__ == "__main__":
    main()
