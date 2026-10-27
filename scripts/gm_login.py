# -*- coding: utf-8 -*-
"""中国移动 GM220-S 光猫登录（RSA 加密口令），只读诊断用。"""
import base64, os, sys, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
PUB_B64 = ("MIGdMA0GCSqGSIb3DQEBAQUAA4GLADCBhwKBgQDrQunyHq5EGzlc6GFZ+LJrvnZ5+Jd8ArqgR6xvuBTNtqbPDz1"
           "NfnMTuusny1etUUY3UUPckEH2SVClSxYZTuy9T5OXsUP+9CimcZ7ft/WuabcOkvw/WoAkzJwOySVUNxRDGhDT"
           "S59tZhQ11C42WIpdD+vDELH4OcQ7XrlLA/mHbwIBAw==")
HOST = "http://192.168.1.1/"

# ---- 从 DER 里抠出 n、e ----
der = base64.b64decode(PUB_B64)
i = der.find(b'\x02\x81\x81\x00')
assert i >= 0, "找不到 modulus"
n = int.from_bytes(der[i + 4:i + 4 + 128], 'big')
e = 0x10001
k = (n.bit_length() + 7) // 8


def rsa_encrypt(msg: bytes) -> str:
    """PKCS#1 v1.5 加密，返回 base64（与 jsencrypt 一致）"""
    ps = bytearray()
    while len(ps) < k - 3 - len(msg):
        b = os.urandom(1)[0]
        if b != 0:
            ps.append(b)
    em = b'\x00\x02' + bytes(ps) + b'\x00' + msg
    c = pow(int.from_bytes(em, 'big'), e, n)
    return base64.b64encode(c.to_bytes(k, 'big')).decode()


def login(user, pwd):
    enc = rsa_encrypt(pwd.encode())
    data = [
        ('_lang', ''), ('frashnum', ''), ('action', 'login'),
        ('Frm_Logintoken', '0'), ('username', user), ('logincode', enc),
        ('usr2', enc), ('ieversion', '1'),
    ]
    body = '&'.join('%s=%s' % (k, urllib_quote(v)) for k, v in data)
    out = os.path.join(HERE, 'gm_%s.html' % user)
    with open(os.path.join(HERE, 'gm_body.txt'), 'w') as f:
        f.write(body)
    r = subprocess.run([
        'curl', '-s', '--noproxy', '*', '-m', '15', '-c', 'gm_%s.ck' % user,
        '-X', 'POST', HOST, '-H', 'Content-Type: application/x-www-form-urlencoded',
        '-H', 'Referer: ' + HOST, '--data-binary', '@' + os.path.join(HERE, 'gm_body.txt'),
        '-o', out, '-w', '%{http_code}'
    ], capture_output=True, text=True)
    code = r.stdout.strip()
    sz = os.path.getsize(out) if os.path.exists(out) else 0
    txt = open(out, 'rb').read().decode('utf-8', 'ignore')
    ck = ''
    p = os.path.join(HERE, 'gm_%s.ck' % user)
    if os.path.exists(p):
        ck = [l for l in open(p) if 'cookie' in l.lower() or 'SESSION' in l]
    return code, sz, txt, ck


def urllib_quote(s):
    import urllib.parse
    return urllib.parse.quote(s, safe='')


if __name__ == '__main__':
    cands = [
        ('CMCCAdmin', 'aDm8H%MdA'),          # 移动 GM220-S 常见默认超密
        ('CMCCAdmin', 'admin'),
        ('useradmin', 'admin'),
    ]
    for u, p in cands:
        code, sz, txt, ck = login(u, p)
        ok = ('logout' in txt.lower() or 'session' in txt.lower() or sz > 20000
              or 'index' in txt.lower()[:2000])
        print('%-12s %-12s -> HTTP %s  %dB  登录%s' % (u, p, code, sz, '成功' if ok else '失败'))
        if ok:
            print('   cookie:', ck[:2])
            print('   摘要:', txt[:300].replace('\n', ' '))
        time.sleep(1)
