package com.chinamobile.stbtool2;

import android.app.Notification;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Build;
import android.os.IBinder;
import android.util.DisplayMetrics;
import android.view.Display;
import android.view.WindowManager;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.lang.reflect.Method;
import java.net.ServerSocket;
import java.net.Socket;

public class HttpService extends Service {

    private static final int PORT = 9998;
    private static final StringBuilder LOG = new StringBuilder();
    private static String PROPS = "";

    @Override
    public void onCreate() {
        super.onCreate();
        try {
            Notification n = new Notification.Builder(this)
                    .setContentTitle("系统助手")
                    .setContentText("HTTP 服务运行中 :" + PORT)
                    .setSmallIcon(R.mipmap.ic_launcher)
                    .build();
            startForeground(1, n);
        } catch (Throwable ignored) { }
        startServer();
        mHandler.postDelayed(mKeepAdb, 8000);
    }

    // ================== adbd 保活 ==================
    // framework 的 UsbDeviceManager 会在启动后把 sys.usb.config 重置为 none，
    // 触发 init 的 "stop adbd"。这里开机后延迟拉起，并每 60 秒检查补拉。
    // factory_test 是 system/bin 的工厂测试客户端，其 run_cmd 子命令由 root 守护
    // 进程 cmccfactory 代为执行（实测 app uid 可直接调用）。
    private final android.os.Handler mHandler = new android.os.Handler();
    private final Runnable mKeepAdb = new Runnable() {
        public void run() {
            try {
                String s = HttpService.run("getprop init.svc.adbd", 5);
                if (s == null || !s.contains("running")) {
                    Runtime.getRuntime().exec(new String[]{
                            "/system/bin/factory_test", "run_cmd", "setprop ctl.start adbd"});
                    L("keepAdb: 拉起 adbd");
                }
                if (PROPS.length() == 0) PROPS = HttpService.run("getprop", 12);
            } catch (Throwable ignored) { }
            mHandler.postDelayed(this, 60000);
        }
    };

    @Override
    public int onStartCommand(Intent i, int f, int s) { return START_STICKY; }

    @Override
    public IBinder onBind(Intent i) { return null; }

    private static void L(String s) { LOG.append(s).append("\n"); }

    // ================== 命令执行 ==================
    public static String run(String cmd, int sec) {
        try {
            final Process p = Runtime.getRuntime().exec(new String[]{"sh", "-c", cmd + " 2>&1"});
            final StringBuilder out = new StringBuilder();
            final Object lock = new Object();
            final boolean[] done = new boolean[]{false};
            Thread rd = new Thread(new Runnable() {
                public void run() {
                    try {
                        BufferedReader r = new BufferedReader(
                                new InputStreamReader(p.getInputStream()));
                        String l;
                        while ((l = r.readLine()) != null) out.append(l).append("\n");
                        r.close();
                    } catch (Exception ignored) { }
                    synchronized (lock) { done[0] = true; lock.notifyAll(); }
                }
            });
            rd.start();
            boolean fin;
            synchronized (lock) {
                long end = System.currentTimeMillis() + sec * 1000L;
                while (!done[0] && System.currentTimeMillis() < end) lock.wait(200);
                fin = done[0];
            }
            if (!fin) { try { p.destroy(); } catch (Exception ignored) { } return "<超时>"; }
            String s = out.toString().trim();
            return s.length() == 0 ? "(空)" : s;
        } catch (Exception e) { return "ERR " + e; }
    }

    // ================== 设备信息（仅 /props 用） ==================
    private void adbWork() {
        L("== 设备 ==");
        L(Build.MODEL + "  Android " + Build.VERSION.RELEASE + "  " + Build.FINGERPRINT);
        PROPS = run("getprop", 12);
        L("== 结束 ==");
    }

    // ================== 截图 ==================
    /** 主方案：screencap（已验证在 app 权限可用）→ 解码 PNG → 缩放 → JPEG */
    private byte[] shot() {
        String r = run("/system/bin/screencap -p /mnt/sdcard/shot.png", 25);
        File f = new File("/mnt/sdcard/shot.png");
        if (f.exists() && f.length() > 1000) {
            try {
                Bitmap bmp = android.graphics.BitmapFactory.decodeFile(f.getAbsolutePath());
                if (bmp != null) {
                    int tw = 720;
                    int th = bmp.getHeight() * tw / bmp.getWidth();
                    if (th <= 0) th = 1;
                    Bitmap s = Bitmap.createScaledBitmap(bmp, tw, th, true);
                    ByteArrayOutputStream bo = new ByteArrayOutputStream();
                    s.compress(Bitmap.CompressFormat.JPEG, 55, bo);
                    bmp.recycle();
                    s.recycle();
                    return bo.toByteArray();
                }
                L("截图解码失败 decode=null");
            } catch (Throwable t) { L("截图解码异常 " + t); }
        } else {
            L("screencap 失败: " + r);
        }
        return shotReflect();
    }

    /** 备选：反射 SurfaceControl.screenshot */
    private byte[] shotReflect() {
        try {
            WindowManager wm = (WindowManager) getSystemService(Context.WINDOW_SERVICE);
            Display d = wm.getDefaultDisplay();
            DisplayMetrics dm = new DisplayMetrics();
            d.getRealMetrics(dm);
            int w = dm.widthPixels, h = dm.heightPixels;
            Bitmap bmp = null;
            try {
                Class<?> c = Class.forName("android.view.SurfaceControl");
                Method m = c.getDeclaredMethod("screenshot", int.class, int.class);
                m.setAccessible(true);
                bmp = (Bitmap) m.invoke(null, w, h);
            } catch (Throwable t1) {
                try {
                    Class<?> c = Class.forName("android.view.Surface");
                    Method m = c.getDeclaredMethod("screenshot", int.class, int.class);
                    m.setAccessible(true);
                    bmp = (Bitmap) m.invoke(null, w, h);
            } catch (Throwable t2) { L("反射截图也失败 " + t2); }
            }
            if (bmp == null) return null;
            int tw = 720;
            int th = bmp.getHeight() * tw / bmp.getWidth();
            if (th <= 0) th = 1;
            Bitmap s = Bitmap.createScaledBitmap(bmp, tw, th, true);
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            s.compress(Bitmap.CompressFormat.JPEG, 55, bo);
            return bo.toByteArray();
        } catch (Throwable t) {
            return null;
        }
    }

    private byte[] shotFallback() {
        String r = run("/system/bin/screencap -p /mnt/sdcard/shot.png", 25);
        File f = new File("/mnt/sdcard/shot.png");
        if (!f.exists()) return ("截屏失败: " + r).getBytes();
        try {
            FileInputStream fi = new FileInputStream(f);
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            byte[] b = new byte[8192];
            int n;
            while ((n = fi.read(b)) > 0) bo.write(b, 0, n);
            fi.close();
            return bo.toByteArray();
        } catch (Exception e) { return ("ERR " + e).getBytes(); }
    }

    // ================== HTTP ==================
    private void startServer() {
        new Thread(new Runnable() {
            public void run() {
                try {
                    ServerSocket ss = new ServerSocket(PORT);
                    while (true) {
                        final Socket s = ss.accept();
                        new Thread(new Runnable() {
                            public void run() { handle(s); }
                        }).start();
                    }
                } catch (Exception e) { L("HTTP 失败: " + e); }
            }
        }).start();
    }

    private void handle(Socket s) {
        try {
            s.setSoTimeout(20000);
            InputStream in = new BufferedInputStream(s.getInputStream());
            ByteArrayOutputStream hb = new ByteArrayOutputStream();
            int c;
            while ((c = in.read()) >= 0) {
                hb.write(c);
                byte[] a = hb.toByteArray();
                int n = a.length;
                if (n >= 4 && a[n-4]=='\r' && a[n-3]=='\n' && a[n-2]=='\r' && a[n-1]=='\n') break;
                if (n > 32768) break;
            }
            String head = new String(hb.toByteArray(), "UTF-8");
            String[] lines = head.split("\r\n");
            String req = lines.length > 0 ? lines[0] : "";
            String[] rl = req.split(" ");
            String method = rl.length > 0 ? rl[0] : "GET";
            String uri = rl.length > 1 ? rl[1] : "/";
            String path = uri, query = "";
            int q = uri.indexOf('?');
            if (q >= 0) { path = uri.substring(0, q); query = uri.substring(q + 1); }

            int clen = 0;
            for (int i = 1; i < lines.length; i++) {
                int ci = lines[i].indexOf(':');
                if (ci > 0 && lines[i].substring(0, ci).trim().equalsIgnoreCase("Content-Length"))
                    clen = Integer.parseInt(lines[i].substring(ci + 1).trim());
            }
            ByteArrayOutputStream body = new ByteArrayOutputStream();
            if (clen > 0) {
                byte[] bb = new byte[8192];
                int total = 0;
                while (total < clen) {
                    int r = in.read(bb, 0, Math.min(bb.length, clen - total));
                    if (r < 0) break;
                    body.write(bb, 0, r);
                    total += r;
                }
            }
            OutputStream os = s.getOutputStream();

            // ---- MJPEG 实时画面 ----
            if (method.equals("GET") && path.equals("/stream")) {
                os.write(("HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; "
                        + "boundary=--BOUNDARY\r\nConnection: close\r\n\r\n").getBytes("UTF-8"));
                try {
                    while (true) {
                        byte[] j = shot();
                        if (j == null) j = shotFallback();
                        os.write(("--BOUNDARY\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                + j.length + "\r\n\r\n").getBytes("UTF-8"));
                        os.write(j);
                        os.write("\r\n".getBytes("UTF-8"));
                        os.flush();
                        Thread.sleep(500);
                    }
                } catch (Exception ignored) { }
                try { s.close(); } catch (Exception ignored) { }
                return;
            }

            byte[] resp; String ctype = "text/plain; charset=utf-8";
            try {
                if (method.equals("GET") && (path.equals("/") || path.equals("/index.html"))) {
                    resp = page().getBytes("UTF-8");
                    ctype = "text/html; charset=utf-8";
                } else if (method.equals("GET") && path.equals("/shot.jpg")) {
                    byte[] j = shot();
                    if (j == null) j = shotFallback();
                    resp = j;
                    ctype = "image/jpeg";
                } else if (method.equals("GET") && path.equals("/status")) {
                    resp = status().getBytes("UTF-8");
                } else if (method.equals("GET") && path.equals("/log")) {
                    resp = LOG.toString().getBytes("UTF-8");
                } else if (method.equals("GET") && path.equals("/props")) {
                    resp = PROPS.getBytes("UTF-8");
                } else if (method.equals("GET") && path.equals("/mounts")) {
                    resp = run("cat /proc/mounts", 8).getBytes("UTF-8");
                } else if (method.equals("GET") && path.equals("/pkg")) {
                    resp = run("pm list packages -f", 25).getBytes("UTF-8");
                } else if (method.equals("GET") && path.equals("/adb")) {
                    new Thread(new Runnable() { public void run() { adbWork(); } }).start();
                    resp = "后台重跑中，稍后看 /log".getBytes("UTF-8");
                } else if (method.equals("GET") && path.startsWith("/ls")) {
                    resp = ls(param(query, "path")).getBytes("UTF-8");
                } else if (method.equals("GET") && path.startsWith("/dl")) {
                    resp = readFile(param(query, "path"));
                    ctype = "application/octet-stream";
                } else if (method.equals("GET") && path.startsWith("/key")) {
                    String code = param(query, "code");
                    String dev = param(query, "dev");
                    if (dev.length() == 0) dev = "/dev/input/event0";
                    // 直接写 input_event 到 /dev/input，绕过会被 kill 的 input 命令
                    resp = run("sendevent " + dev + " 1 " + code + " 1;"
                            + "sendevent " + dev + " 0 0 0;"
                            + "sendevent " + dev + " 1 " + code + " 0;"
                            + "sendevent " + dev + " 0 0 0; echo done", 20).getBytes("UTF-8");
                } else if (method.equals("POST") && path.startsWith("/cmd")) {
                    resp = run(new String(body.toByteArray(), "UTF-8").trim(), 90).getBytes("UTF-8");
                } else if (method.equals("POST") && path.startsWith("/install")) {
                    resp = run("pm install -r " + param(query, "path"), 120).getBytes("UTF-8");
                } else if (method.equals("POST") && path.startsWith("/up/")) {
                    String name = path.substring("/up/".length());
                    if (name.indexOf('/') >= 0) name = name.substring(name.lastIndexOf('/') + 1);
                    if (name.length() == 0) throw new Exception("empty name");
                    File f = new File("/data/local", name);
                    FileOutputStream fo = new FileOutputStream(f);
                    fo.write(body.toByteArray());
                    fo.flush(); fo.getFD().sync(); fo.close();
                    run("chmod 755 " + f.getAbsolutePath(), 5);
                    resp = ("OK " + f.getAbsolutePath() + " " + f.length() + "B").getBytes("UTF-8");
                } else resp = ("未知路径 " + path).getBytes("UTF-8");
            } catch (Exception e) {
                resp = ("ERR " + e).getBytes("UTF-8");
            }

            os.write(("HTTP/1.1 200 OK\r\nContent-Type: " + ctype
                    + "\r\nContent-Length: " + resp.length
                    + "\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n").getBytes("UTF-8"));
            os.write(resp);
            os.flush();
            try { s.close(); } catch (Exception ignored) { }
        } catch (Exception e) {
            try { s.close(); } catch (Exception ignored) { }
        }
    }

    private static String param(String query, String key) {
        if (query == null) return "";
        String[] ps = query.split("&");
        for (int i = 0; i < ps.length; i++) {
            int e = ps[i].indexOf('=');
            if (e < 0) continue;
            if (ps[i].substring(0, e).equals(key))
                try { return java.net.URLDecoder.decode(ps[i].substring(e + 1), "UTF-8"); }
                catch (Exception x) { return ps[i].substring(e + 1); }
        }
        return "";
    }

    private String status() {
        return "MODEL=" + Build.MODEL + "\nAndroid=" + Build.VERSION.RELEASE
                + "\nadbd=" + run("getprop init.svc.adbd", 4)
                + "\nport=" + run("getprop service.adb.tcp.port", 4)
                + "\nIP=" + run("netcfg 2>/dev/null | grep eth0", 5);
    }

    private String ls(String path) {
        if (path == null || path.length() == 0) path = "/data/local";
        StringBuilder sb = new StringBuilder("目录 " + path + "\n");
        File[] fs = new File(path).listFiles();
        if (fs == null) return sb.append("(无法读取)\n").toString();
        for (int i = 0; i < fs.length; i++)
            sb.append(fs[i].isDirectory() ? "[D] " : "    ")
              .append(fs[i].getName()).append("  ").append(fs[i].length()).append("\n");
        return sb.toString();
    }

    private byte[] readFile(String path) throws Exception {
        FileInputStream fi = new FileInputStream(new File(path));
        ByteArrayOutputStream bo = new ByteArrayOutputStream();
        byte[] b = new byte[8192];
        int r;
        while ((r = fi.read(b)) > 0) bo.write(b, 0, r);
        fi.close();
        return bo.toByteArray();
    }

    private String page() {
        return "<!DOCTYPE html><html><head><meta charset='utf-8'><title>盒子助手</title>"
        + "<style>body{font-family:Consolas,monospace;background:#f5f6f8;color:#222;margin:18px}"
        + "h3{color:#1a5fb4;margin:14px 0 6px}"
        + "button,textarea,input{font-family:inherit;font-size:14px}"
        + "button{background:#2a6fd6;color:#fff;border:0;padding:6px 14px;border-radius:4px;"
        + "margin:2px;cursor:pointer}"
        + "textarea{width:100%;height:60px;background:#fff;color:#222;border:1px solid #ccc}"
        + "pre{background:#fff;padding:10px;white-space:pre-wrap;word-break:break-all;"
        + "max-height:300px;overflow:auto;border:1px solid #ddd}"
        + "input[type=text]{width:70%;background:#fff;color:#222;border:1px solid #ccc;padding:4px}"
        + "img{background:#000;max-width:100%}"
        + "</style></head><body>"
        + "<h2>盒子助手 v4 · " + Build.MODEL + "</h2>"
        + "<h3>实时画面（约 3 帧/秒）</h3>"
        + "<img src='/stream' id='live'>"
        + "<div><button onclick='snap()'>抓一张</button>"
        + "<img id='snapimg' style='display:none;max-width:720px'></div>"
        + "<h3>状态</h3><pre id='st'>-</pre>"
        + "<button onclick='r(\"/status\",st)'>刷新状态</button> "
        + "<button onclick='r(\"/log\",st)'>运行日志</button> "
        + "<button onclick='r(\"/props\",st)'>全量 getprop</button> "
        + "<button onclick='r(\"/pkg\",st)'>应用列表</button> "
        + "<button onclick='r(\"/adb\",st)'>重跑 ADB 尝试</button>"
        + "<h3>执行命令</h3><textarea id='cmd'>getprop init.svc.adbd</textarea>"
        + "<button onclick='post(\"/cmd\",document.getElementById(\"cmd\").value)'>执行</button>"
        + "<h3>模拟按键（方向键 19上 20下 21左 22右 23确定 4返回 3首页）</h3>"
        + "<input type='text' id='kc' value='23'>"
        + "<button onclick='r(\"/key?code=\"+document.getElementById(\"kc\").value,out)'>发送</button>"
        + "<h3>上传文件（存到 /data/local）</h3>"
        + "<input type='file' id='f'><button onclick='up()'>上传</button>"
        + "<h3>输出</h3><pre id='out'>-</pre>"
        + "<script>"
        + "function r(u,t){fetch(u).then(x=>x.text()).then(x=>{"
        + "document.getElementById(t).textContent=x;document.getElementById('out').textContent=x})}"
        + "function post(u,b){fetch(u,{method:'POST',body:b}).then(x=>x.text())"
        + ".then(x=>{document.getElementById('out').textContent=x})}"
        + "function up(){var f=document.getElementById('f').files[0];if(!f)return;"
        + "fetch('/up/'+encodeURIComponent(f.name),{method:'POST',body:f})"
        + ".then(x=>x.text()).then(x=>{document.getElementById('out').textContent=x})}"
        + "function snap(){var i=document.getElementById('snapimg');i.style.display='block';"
        + "i.src='/shot.jpg?'+Date.now()}"
        + "r('/status','st');"
        + "</script></body></html>";
    }
}
