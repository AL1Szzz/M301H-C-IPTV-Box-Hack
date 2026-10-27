package app.orchard.tv4;

import java.io.DataOutputStream;
import java.io.InputStream;

/**
 * 执行冻结 / 解冻所需的命令。
 *
 * 策略：优先直接执行（本 App 装成系统应用后，pm 直接就能用，
 * 完全不会弹出 SuperSU 授权框）；只有直连失败时才回退到 su。
 * 读取冻结列表时绝不走 su —— 否则每次启动桌面都会弹授权框，
 * 把遥控器的焦点整个吃掉。
 */
public final class RootCmd {

    /** 冻结：禁止运行，彻底锁住后台 */
    public static boolean freeze(String pkg) {
        // 先试直连（系统应用路径，无弹窗）
        runDirect("pm disable-user --user 0 " + pkg);
        if (isDisabled(pkg)) return true;
        runDirect("pm disable " + pkg);
        if (isDisabled(pkg)) return true;

        // 回退 factory_test 后门（移动盒子 cmccfactory root 守护）
        runFactory("pm disable-user --user 0 " + pkg);
        if (isDisabled(pkg)) return true;
        runFactory("pm disable " + pkg);
        if (isDisabled(pkg)) return true;

        // 最后回退 su（这时用户正在操作，弹授权框是合理的）
        runSu("pm disable-user --user 0 " + pkg);
        if (isDisabled(pkg)) return true;
        runSu("pm disable " + pkg);
        return isDisabled(pkg);
    }

    /** 解冻 */
    public static boolean unfreeze(String pkg) {
        runDirect("pm enable " + pkg);
        if (!isDisabled(pkg)) return true;
        runFactory("pm enable " + pkg);
        if (!isDisabled(pkg)) return true;
        runSu("pm enable " + pkg);
        return !isDisabled(pkg);
    }

    /** 读取当前被禁用（冻结）的包名列表。只读，绝不触发 su。 */
    public static String listDisabled() {
        Result r = runDirect("pm list packages -d");
        if (!r.ok || r.out == null || r.out.trim().length() == 0) {
            r = runFactory("pm list packages -d");
        }
        return r.ok ? r.out : "";
    }

    /** 是否有 root 能力。会触发一次 su，只在用户主动冻结时调用。 */
    public static boolean available() {
        Result r = runSu("id");
        return r.ok && r.out != null && r.out.contains("uid=0");
    }

    /** 是否有「不经 su 直接操作 pm」的能力（装成系统应用后为 true） */
    public static boolean privileged() {
        Result r = runDirect("pm list packages -d");
        return r.ok;
    }

    private static boolean isDisabled(String pkg) {
        String s = listDisabled();
        if (s == null || s.length() == 0) return false;
        for (String line : s.split("\n")) {
            String t = line.trim();
            if (t.equals("package:" + pkg)) return true;
        }
        return false;
    }

    // ------------------------------------------------------------- 执行

    public static class Result {
        public boolean ok;
        public String out = "";
        public String err = "";
    }

    public static Result runDirect(String cmd) {
        Result res = new Result();
        Process p = null;
        try {
            // 追加一行退出码，避免「失败但返回 0」的误判
            p = Runtime.getRuntime().exec(new String[]{"sh", "-c", cmd + " 2>&1; echo __EXIT__$?"});
            res.out = drain(p.getInputStream());
            int code = parseExit(res.out);
            res.out = stripExit(res.out);
            res.ok = (code == 0);
        } catch (Throwable t) {
            res.ok = false;
            res.err = String.valueOf(t);
        } finally {
            if (p != null) {
                try { p.destroy(); } catch (Throwable ignored) { }
            }
        }
        return res;
    }

    public static Result runSu(String cmd) {
        Result res = new Result();
        Process p = null;
        try {
            p = Runtime.getRuntime().exec("su");
            DataOutputStream os = new DataOutputStream(p.getOutputStream());
            os.writeBytes(cmd + "\n");
            os.writeBytes("echo __EXIT__$?\n");
            os.writeBytes("exit\n");
            os.flush();
            res.out = drain(p.getInputStream());
            res.err = drain(p.getErrorStream());
            int code = parseExit(res.out);
            res.out = stripExit(res.out);
            res.ok = (code == 0);
            if (res.ok && res.err != null && res.err.contains("not allowed")) {
                res.ok = false;
            }
        } catch (Throwable t) {
            res.ok = false;
            res.err = String.valueOf(t);
        } finally {
            if (p != null) {
                try { p.destroy(); } catch (Throwable ignored) { }
            }
        }
        return res;
    }

    /**
     * 移动盒子专属：factory_test run_cmd 走 cmccfactory root 守护，
     * 任何 app uid 都能调，等价 root 执行。输出无 __EXIT__ 标记，
     * 以「有没有合理输出」判断成功。
     */
    public static Result runFactory(String cmd) {
        Result res = new Result();
        Process p = null;
        try {
            p = Runtime.getRuntime().exec(new String[]{"/system/bin/factory_test", "run_cmd", cmd});
            res.out = drain(p.getInputStream());
            res.err = drain(p.getErrorStream());
            res.ok = res.out != null && res.out.trim().length() > 0;
        } catch (Throwable t) {
            res.ok = false;
            res.err = String.valueOf(t);
        } finally {
            if (p != null) {
                try { p.destroy(); } catch (Throwable ignored) { }
            }
        }
        return res;
    }

    private static int parseExit(String out) {
        int i = out.lastIndexOf("__EXIT__");
        if (i < 0) return -1;
        String tail = out.substring(i + 8).trim();
        try {
            return Integer.parseInt(tail);
        } catch (Throwable t) {
            return -1;
        }
    }

    private static String stripExit(String out) {
        int i = out.lastIndexOf("__EXIT__");
        return i < 0 ? out : out.substring(0, i);
    }

    private static String drain(InputStream in) {
        StringBuilder sb = new StringBuilder();
        try {
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) > 0) {
                sb.append(new String(buf, 0, n, "UTF-8"));
            }
        } catch (Throwable ignored) { }
        return sb.toString();
    }
}
