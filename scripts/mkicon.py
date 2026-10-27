# -*- coding: utf-8 -*-
"""生成纯 PNG 启动图标（不依赖 PIL），避免 Android 4.4 矢量图/无图标问题"""
import zlib, struct, os, math

def png(path, size, bg=(26,115,232), fg=(255,255,255)):
    cx = cy = (size-1)/2.0
    r_out = size*0.36
    r_in  = size*0.22
    rows = []
    for y in range(size):
        row = bytearray([0])  # filter type 0
        for x in range(size):
            d = math.hypot(x-cx, y-cy)
            if d <= r_in or (r_out-1.5 <= d <= r_out+1.5):
                row += bytes(fg + (255,))
            else:
                row += bytes(bg + (255,))
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t+d) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)
    return len(data)

for proj in (r"F:/AK50/03_桌面源码/stbtool", r"F:/AK50/03_桌面源码/stbhello"):
    for dpi, s in (("mdpi",48),("hdpi",72),("xhdpi",96),("xxhdpi",144)):
        p = os.path.join(proj, "app", "src", "main", "res", "mipmap-"+dpi, "ic_launcher.png")
        print("%s %dpx %d bytes" % (os.path.basename(proj), s, png(p, s)))
