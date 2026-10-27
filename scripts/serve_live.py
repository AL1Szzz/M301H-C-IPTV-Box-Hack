# -*- coding: utf-8 -*-
"""给电视提供直播源列表的本地 HTTP 服务（局域网）"""
import http.server, socketserver, os, sys

PORT = 8000
DIR = r'F:\AK50\05_直播源'


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write('[%s] %s\n' % (self.address_string(), fmt % args))


class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == '__main__':
    os.chdir(DIR)
    with S(('0.0.0.0', PORT), H) as httpd:
        print('serving %s on 0.0.0.0:%d' % (DIR, PORT))
        sys.stdout.flush()
        httpd.serve_forever()
