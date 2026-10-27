# -*- coding: utf-8 -*-
"""把 AK50 工程整理成一个可公开的 GitHub 仓库副本（自动脱敏）。

复制范围：02_脚本 / 03_桌面源码(仅源码) / 关键文档
排除：build、.gradle、APK、抓包、分区备份、刷机固件、大工具
脱敏：手机号 / MAC / STBID / IPv6 / 真实直播 URL
"""
import os, re, shutil

SRC = r'F:\AK50'
DST = r'F:\AK50\github_repo\M301H-C-Hack'

# ---------- 脱敏规则 ----------
RULES = [
    (r'<你的宽带手机号>', '<你的宽带手机号>'),
    (r'<盒子MAC>', '<盒子MAC>'),
    (r'<电视MAC-有线>', '<电视MAC-有线>'),
    (r'<电视MAC-WiFi>', '<电视MAC-WiFi>'),
    (r'<你的STBID>', '<你的STBID>'),
    (r'2409:8a20:[0-9a-f:]+', '<你的IPv6前缀>'),
    (r'\b112\.22\.\d+\.\d+', '<你的公网IP>'),
]
TEXT_EXT = {'.md', '.py', '.java', '.xml', '.gradle', '.txt', '.json', '.m3u',
            '.properties', '.yml', '.sh', '.cfg', '.html'}
SKIP_DIR = {'build', '.gradle', '.idea', 'bak', 'cap', 'streams', 'streams2',
            'streams3', 'streams4', 'streams5', 'resp', 'resp2', 'bak'}
SKIP_EXT = {'.apk', '.jar', '.png', '.jpg', '.pcap', '.img', '.bin', '.zip',
            '.db', '.so', '.dex', '.gz', '.tar', '.ck'}


def desens(s):
    for pat, rep in RULES:
        s = re.sub(pat, rep, s)
    return s


def copy_tree(rel_src, rel_dst, only_ext=None):
    src = os.path.join(SRC, rel_src)
    dst = os.path.join(DST, rel_dst)
    n = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR and not d.startswith('.')]
        rel = os.path.relpath(root, src)
        out_dir = dst if rel == '.' else os.path.join(dst, rel)
        os.makedirs(out_dir, exist_ok=True)
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_EXT:
                continue
            if only_ext and ext not in only_ext:
                continue
            p = os.path.join(root, f)
            o = os.path.join(out_dir, f)
            try:
                if ext in TEXT_EXT:
                    t = open(p, encoding='utf-8', errors='ignore').read()
                    open(o, 'w', encoding='utf-8').write(desens(t))
                else:
                    shutil.copy2(p, o)
                n += 1
            except Exception as e:
                print('  skip', p, e)
    print('%-40s -> %d 文件' % (rel_src, n))


def copy_file(rel_src, rel_dst):
    src = os.path.join(SRC, rel_src)
    dst = os.path.join(DST, rel_dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    t = open(src, encoding='utf-8', errors='ignore').read()
    open(dst, 'w', encoding='utf-8').write(desens(t))
    print('%-40s -> ok' % rel_src)


if os.path.exists(DST):
    shutil.rmtree(DST)
os.makedirs(DST)

copy_tree(r'02_脚本', 'scripts')
copy_tree(r'03_桌面源码\launcher', 'app/AerialTV4')
copy_tree(r'03_桌面源码\livetv', 'app/AK直播')
copy_tree(r'03_桌面源码\stbtool2', 'app/StbTool2')
copy_tree(r'03_桌面源码\stbhello', 'app/StbHello')

for f in ['00_盒子攻防报告.md']:
    if os.path.exists(os.path.join(SRC, f)):
        copy_file(f, 'docs/' + f)

# 系统快照里的纯文档
snap = os.path.join(SRC, r'06_系统快照')
for root, dirs, files in os.walk(snap):
    dirs[:] = [d for d in dirs if d not in SKIP_DIR]
    for f in files:
        if f.endswith('.md'):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, snap)
            copy_file(os.path.join('06_系统快照', rel), os.path.join('docs', '06_系统快照', rel))

# live.m3u 里含真实播放地址 -> 替换成模板
for m3u in [os.path.join(DST, r'app\AK直播\app\src\main\assets\live.m3u')]:
    if os.path.exists(m3u):
        open(m3u, 'w', encoding='utf-8').write(
            "#EXTM3U\n"
            "# 说明：这里原本是本机的真实直播源（含账号级 token，已脱敏移除）。\n"
            "# 请用 scripts/gen_live_m3u.py 按 docs/04-IPTV直播源逆向.md 的步骤生成你自己的。\n"
            "# 下面两行是公开示例，仅用于验证播放器能否加载列表：\n"
            "#EXTINF:-1 group-title=\"示例\",示例频道\n"
            "http://example.com/stream.m3u8\n")

print('\n完成:', DST)
for root, dirs, files in os.walk(DST):
    dirs[:] = [d for d in dirs if d != '.git']
    n = len(files)
    if n:
        print(' ', os.path.relpath(root, DST), n)
