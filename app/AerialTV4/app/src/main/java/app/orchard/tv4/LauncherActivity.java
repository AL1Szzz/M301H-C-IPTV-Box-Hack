package app.orchard.tv4;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.WallpaperManager;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.provider.Settings;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileFilter;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * 仿 Aerial 风格的极简电视桌面（Android 4.4 / API 19 可用）。
 *
 * 焦点策略：不依赖系统焦点机制（老 4.4 设备上经常建立不起来），
 * 而是在 dispatchKeyEvent 里自己接管方向键 / 确认键 / 菜单键，
 * 自己维护 selPos 并刷新高亮。这样任何遥控器都能用。
 *
 * 另外把「冰箱」的核心能力做进来了 —— 菜单键可以对应用冻结 / 解冻，
 * 冻结后它无法自启、无法被互相唤醒，图标上会挂一个红色角标。
 */
public class LauncherActivity extends Activity {

    private static final String TAG = "AT4";
    /** 「已锁住的应用」入口用的假包名 */
    private static final String VAULT_PKG = "__frozen_vault__";

    private GridView grid;
    private TextView clockView;
    private TextView dateView;
    private TextView hintView;
    private ImageView wallpaperView;

    private Prefs prefs;
    private final List<AppEntry> apps = new ArrayList<AppEntry>();
    /** 所有处于冻结状态的应用，供「已锁住」入口展示与解冻 */
    private final List<AppEntry> frozenApps = new ArrayList<AppEntry>();
    private AppAdapter adapter;
    private final Handler handler = new Handler();
    private boolean hasRoot = false;

    private int selPos = 0;
    private boolean centerHeld = false;
    private boolean longPressFired = false;

    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            updateClock();
            handler.postDelayed(this, 1000);
        }
    };

    /** 长按确认键 → 打开应用菜单 */
    private final Runnable longPress = new Runnable() {
        @Override
        public void run() {
            if (centerHeld) {
                centerHeld = false;
                longPressFired = true;
                AppEntry e = current();
                if (e != null) showAppMenu(e);
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_launcher);

        prefs = new Prefs(this);
        grid = (GridView) findViewById(R.id.grid);
        clockView = (TextView) findViewById(R.id.clock);
        dateView = (TextView) findViewById(R.id.date);
        hintView = (TextView) findViewById(R.id.hint);
        wallpaperView = (ImageView) findViewById(R.id.wallpaper);

        loadWallpaper();
        reload();

        grid.setNumColumns(prefs.getColumns());
        adapter = new AppAdapter(this, apps);
        grid.setAdapter(adapter);

        // 让 GridView 不参与焦点竞争，全交给 dispatchKeyEvent
        grid.setFocusable(false);
        grid.setFocusableInTouchMode(false);

        grid.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                selPos = position;
                applySelection();
                launch(apps.get(position));
            }
        });

        grid.setOnItemLongClickListener(new AdapterView.OnItemLongClickListener() {
            @Override
            public boolean onItemLongClick(AdapterView<?> parent, View view, int position, long id) {
                selPos = position;
                applySelection();
                showAppMenu(apps.get(position));
                return true;
            }
        });

        updateClock();
        handler.postDelayed(tick, 1000);

        // 首屏后把初始选中高亮刷出来
        handler.post(new Runnable() {
            @Override
            public void run() {
                clampSel();
                applySelection();
            }
        });

        // 注意：这里【不要】在启动时探测 root。
        // 一旦调 su 就会弹出 SuperSU 授权框，它会盖在桌面上把遥控器焦点整个吃掉，
        // 表现为「按方向键没反应」。root 改成等用户真的要冻结时再探测。
    }

    /** 前台标志：MenuKeyService 用它判断菜单键是否该转交给自己 */
    public static volatile boolean sForeground = false;

    @Override
    protected void onResume() {
        super.onResume();
        sForeground = true;
        // 延迟刷新，避免阻塞 resume 造成按键卡顿
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                reload();
                adapter.notifyDataSetChanged();
                clampSel();
                applySelection();
            }
        }, 350);
    }

    @Override
    protected void onPause() {
        sForeground = false;
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacks(tick);
        handler.removeCallbacks(longPress);
        super.onDestroy();
    }

    // ------------------------------------------------------- 按键（自己接管）

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        int action = event.getAction();
        int code = event.getKeyCode();

        if (action == KeyEvent.ACTION_DOWN) {
            switch (code) {
                case KeyEvent.KEYCODE_DPAD_LEFT:
                    move(-1);
                    return true;
                case KeyEvent.KEYCODE_DPAD_RIGHT:
                    move(1);
                    return true;
                case KeyEvent.KEYCODE_DPAD_UP:
                    move(-columns());
                    return true;
                case KeyEvent.KEYCODE_DPAD_DOWN:
                    move(columns());
                    return true;
                case KeyEvent.KEYCODE_PAGE_UP:
                case KeyEvent.KEYCODE_CHANNEL_UP:
                    move(-columns() * 3);
                    return true;
                case KeyEvent.KEYCODE_PAGE_DOWN:
                case KeyEvent.KEYCODE_CHANNEL_DOWN:
                    move(columns() * 3);
                    return true;
                case KeyEvent.KEYCODE_MOVE_HOME:
                    selPos = 0;
                    applySelection();
                    return true;
                case KeyEvent.KEYCODE_MOVE_END:
                    selPos = Math.max(0, apps.size() - 1);
                    applySelection();
                    return true;
                case KeyEvent.KEYCODE_DPAD_CENTER:
                case KeyEvent.KEYCODE_ENTER:
                case KeyEvent.KEYCODE_NUMPAD_ENTER:
                    if (event.getRepeatCount() == 0) {
                        centerHeld = true;
                        longPressFired = false;
                        handler.postDelayed(longPress, 550);
                    }
                    return true;
                case KeyEvent.KEYCODE_MENU:
                    AppEntry e = current();
                    if (e != null) showAppMenu(e);
                    else showGlobalMenu();
                    return true;
            }
        } else if (action == KeyEvent.ACTION_UP) {
            if (code == KeyEvent.KEYCODE_DPAD_CENTER
                    || code == KeyEvent.KEYCODE_ENTER
                    || code == KeyEvent.KEYCODE_NUMPAD_ENTER) {
                handler.removeCallbacks(longPress);
                if (centerHeld && !longPressFired) {
                    centerHeld = false;
                    AppEntry e = current();
                    if (e != null) launch(e);
                }
                centerHeld = false;
                return true;
            }
        }
        return super.dispatchKeyEvent(event);
    }

    private int columns() {
        int c = prefs.getColumns();
        return c <= 0 ? 6 : c;
    }

    private AppEntry current() {
        if (apps.isEmpty()) return null;
        clampSel();
        return apps.get(selPos);
    }

    private void clampSel() {
        if (apps.isEmpty()) {
            selPos = 0;
            return;
        }
        if (selPos < 0) selPos = 0;
        if (selPos > apps.size() - 1) selPos = apps.size() - 1;
    }

    private void move(int delta) {
        if (apps.isEmpty()) return;
        clampSel();
        int next = selPos + delta;
        if (next < 0) next = 0;
        if (next > apps.size() - 1) next = apps.size() - 1;
        if (next == selPos) return;
        selPos = next;
        if (apps.size() > selPos) {
            Log.d(TAG, "move -> sel=" + selPos + "/" + apps.size() + " " + apps.get(selPos).label);
        }
        applySelection();
    }

    /** 刷新选中高亮（只遍历可见 child，不重排、不丢滚动位置） */
    private void applySelection() {
        clampSel();
        if (adapter != null) adapter.setSelection(selPos);
        if (grid == null) return;

        int first = grid.getFirstVisiblePosition();
        int n = grid.getChildCount();
        for (int i = 0; i < n; i++) {
            View v = grid.getChildAt(i);
            if (v == null) continue;
            int pos = first + i;
            AppEntry e = (pos >= 0 && pos < apps.size()) ? apps.get(pos) : null;
            AppAdapter.decorate(v, pos == selPos, e != null && e.frozen);
        }

        // 保证选中项滚进可视区
        if (selPos < first || selPos >= first + n) {
            grid.setSelection(selPos);
            handler.post(new Runnable() {
                @Override
                public void run() {
                    int f = grid.getFirstVisiblePosition();
                    int c = grid.getChildCount();
                    for (int i = 0; i < c; i++) {
                        View v = grid.getChildAt(i);
                        if (v == null) continue;
                        int pos = f + i;
                        AppEntry e = (pos >= 0 && pos < apps.size()) ? apps.get(pos) : null;
                        AppAdapter.decorate(v, pos == selPos, e != null && e.frozen);
                    }
                }
            });
        }

        if (hintView != null && !apps.isEmpty()) {
            AppEntry e = apps.get(selPos);
            if (e.vault) {
                hintView.setText("确认键：查看被锁住的应用，可单个或全部解冻");
            } else {
                hintView.setText((selPos + 1) + "/" + apps.size() + "  " + e.label
                        + (e.frozen ? "  （已锁住）" : ""));
            }
        }
    }

    // ---------------------------------------------------------------- 数据

    private void reload() {
        apps.clear();
        frozenApps.clear();
        PackageManager pm = getPackageManager();
        Set<String> hidden = new HashSet<String>(prefs.getHidden());
        Set<String> disabled = parseDisabled(RootCmd.listDisabled());
        String self = getPackageName();
        boolean hideFrozen = prefs.getHideFrozen();

        List<PackageInfo> installed = pm.getInstalledPackages(0);
        Set<String> seen = new HashSet<String>();
        Set<String> frozenSeen = new HashSet<String>();

        for (PackageInfo pi : installed) {
            String pkg = pi.packageName;
            if (pkg == null || pkg.equals(self) || seen.contains(pkg)) continue;

            Intent launch = pm.getLaunchIntentForPackage(pkg);
            boolean frozen = disabled.contains(pkg);
            // 被冻结的应用拿不到 launch intent，但仍要收进「已锁住」清单，否则没法解冻
            if (launch == null && !frozen) continue;
            if (hidden.contains(pkg)) continue;

            AppEntry e = makeEntry(pm, pkg, isSystem(pi));
            e.frozen = frozen;

            if (frozen) {
                frozenApps.add(e);
                frozenSeen.add(pkg);
                if (hideFrozen) continue;   // 冻结的不占桌面位置
            }
            apps.add(e);
            seen.add(pkg);
        }

        // 系统里被禁用、但上面没扫到的，也补进「已锁住」清单（保证能解冻）
        for (String pkg : disabled) {
            if (frozenSeen.contains(pkg) || pkg.equals(self) || hidden.contains(pkg)) continue;
            AppEntry e = makeEntry(pm, pkg, true);
            e.frozen = true;
            frozenApps.add(e);
            frozenSeen.add(pkg);
            if (!hideFrozen && !seen.contains(pkg)) {
                apps.add(e);
                seen.add(pkg);
            }
        }

        Collections.sort(apps, new Comparator<AppEntry>() {
            @Override
            public int compare(AppEntry a, AppEntry b) {
                // 冻结的排后面，其余按名称
                if (a.frozen != b.frozen) return a.frozen ? 1 : -1;
                return a.label.compareToIgnoreCase(b.label);
            }
        });

        Collections.sort(frozenApps, new Comparator<AppEntry>() {
            @Override
            public int compare(AppEntry a, AppEntry b) {
                return a.label.compareToIgnoreCase(b.label);
            }
        });

        // 「已锁住」管理入口放在最前面，遥控器左右上下就能选到
        if (!frozenApps.isEmpty()) {
            AppEntry v = new AppEntry(VAULT_PKG, "已锁住 " + frozenApps.size() + " 个", null, false);
            v.vault = true;
            apps.add(0, v);
        }

        Log.d(TAG, "reload: 桌面 " + apps.size() + " 项（含入口），锁住 "
                + frozenApps.size() + " 个，首项=" + (apps.isEmpty() ? "-" : apps.get(0).label)
                + "，锁住项是否上桌面=" + !prefs.getHideFrozen());
    }

    private static AppEntry makeEntry(PackageManager pm, String pkg, boolean system) {
        String label = pkg;
        Drawable icon = null;
        try {
            ApplicationInfo ai = pm.getApplicationInfo(pkg, 0);
            String l = pm.getApplicationLabel(ai).toString();
            if (l != null && l.length() > 0) label = l;
            icon = pm.getApplicationIcon(ai);
        } catch (Throwable ignored) { }
        return new AppEntry(pkg, label, icon, system);
    }

    private static boolean isSystem(PackageInfo pi) {
        return pi.applicationInfo != null
                && (pi.applicationInfo.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
    }

    private static Set<String> parseDisabled(String raw) {
        Set<String> s = new HashSet<String>();
        if (raw == null) return s;
        for (String line : raw.split("\n")) {
            String t = line.trim();
            if (t.startsWith("package:")) {
                s.add(t.substring("package:".length()).trim());
            }
        }
        return s;
    }

    // ---------------------------------------------------------------- 交互

    private void launch(AppEntry e) {
        if (e.vault) {
            showFrozenVault();
            return;
        }
        if (e.frozen) {
            confirmUnfreeze(e);
            return;
        }
        Intent i = getPackageManager().getLaunchIntentForPackage(e.pkg);
        if (i != null) {
            try {
                startActivity(i);
            } catch (Throwable t) {
                toast("打不开：" + e.label);
            }
        } else {
            toast("这个应用没有可启动的界面");
        }
    }

    private void showAppMenu(final AppEntry e) {
        if (e.vault) {
            showFrozenVault();
            return;
        }
        List<String> items = new ArrayList<String>();
        items.add(getString(R.string.action_open));
        if (e.frozen) {
            items.add(getString(R.string.action_unfreeze));
        } else {
            items.add(getString(R.string.action_freeze));
        }
        items.add(getString(R.string.action_hide));
        items.add(getString(R.string.action_info));
        items.add(getString(R.string.action_uninstall));
        items.add("桌面设置…");
        final String[] arr = items.toArray(new String[items.size()]);

        new AlertDialog.Builder(this)
                .setTitle(e.label)
                .setItems(arr, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        String act = arr[which];
                        if (act.equals(getString(R.string.action_open))) {
                            if (e.frozen) {
                                confirmUnfreeze(e);
                            } else {
                                Intent i = getPackageManager().getLaunchIntentForPackage(e.pkg);
                                if (i != null) startActivity(i);
                            }
                        } else if (act.equals(getString(R.string.action_freeze))) {
                            doFreeze(e);
                        } else if (act.equals(getString(R.string.action_unfreeze))) {
                            doUnfreeze(e);
                        } else if (act.equals(getString(R.string.action_hide))) {
                            prefs.addHidden(e.pkg);
                            refresh();
                            toast("已从桌面隐藏（可在桌面设置里恢复）");
                        } else if (act.equals(getString(R.string.action_info))) {
                            Intent i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                    Uri.parse("package:" + e.pkg));
                            try { startActivity(i); } catch (Throwable ignored) { }
                        } else if (act.equals(getString(R.string.action_uninstall))) {
                            Intent i = new Intent(Intent.ACTION_DELETE,
                                    Uri.parse("package:" + e.pkg));
                            try { startActivity(i); } catch (Throwable ignored) { }
                        } else {
                            showGlobalMenu();
                        }
                    }
                })
                .show();
    }

    private void confirmUnfreeze(final AppEntry e) {
        new AlertDialog.Builder(this)
                .setTitle(e.label)
                .setMessage("这个应用已被锁住（冻结）。要解冻吗？")
                .setPositiveButton("解冻", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        doUnfreeze(e);
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }

    private void doFreeze(final AppEntry e) {
        if (e.system && !e.pkg.startsWith("com.konka")) {
            new AlertDialog.Builder(this)
                    .setTitle("确认锁住？")
                    .setMessage(e.label + " 看起来是系统组件，冻结后可能影响电视功能。确定吗？")
                    .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface d, int w) {
                            runFreeze(e);
                        }
                    })
                    .setNegativeButton("取消", null)
                    .show();
        } else {
            runFreeze(e);
        }
    }

    private void runFreeze(final AppEntry e) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                // 直连失败才需要 su，这时弹授权框是合理的（用户正在操作）
                final boolean ok = RootCmd.freeze(e.pkg);
                hasRoot = RootCmd.available();
                handler.post(new Runnable() {
                    @Override
                    public void run() {
                        toast(ok ? ("已锁住：" + e.label + "（可在桌面第一个入口找回）")
                                : ("失败，权限不足：" + e.label));
                        refresh();
                    }
                });
            }
        }).start();
    }

    private void doUnfreeze(final AppEntry e) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                final boolean ok = RootCmd.unfreeze(e.pkg);
                handler.post(new Runnable() {
                    @Override
                    public void run() {
                        toast(ok ? ("已解冻：" + e.label) : ("失败，需要 root：" + e.label));
                        refresh();
                    }
                });
            }
        }).start();
    }

    private void refresh() {
        reload();
        adapter.notifyDataSetChanged();
        clampSel();
        applySelection();
    }

    // ---------------------------------------------------------------- 全局菜单

    private void showGlobalMenu() {
        int nFrozen = frozenApps.size();
        final String[] items = new String[]{
                "回到系统桌面（点播/直播/影视）",
                "系统桌面工具（导航管理/我的应用/开机方式）",
                "已锁住的应用（" + nFrozen + "）",
                "桌面显示锁住的应用：" + (prefs.getHideFrozen() ? "否" : "是"),
                getString(R.string.menu_manage_hidden),
                "解冻全部（恢复所有被锁住的应用）",
                getString(R.string.menu_columns) + "（当前 " + prefs.getColumns() + "）",
                getString(R.string.menu_refresh),
                "换壁纸…",
                getString(R.string.menu_about)
        };
        new AlertDialog.Builder(this)
                .setTitle("Aerial TV 4")
                .setItems(items, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        switch (which) {
                            case 0: goSystemHome(); break;
                            case 1: showSystemDeskTools(); break;
                            case 2: showFrozenVault(); break;
                            case 3:
                                prefs.setHideFrozen(!prefs.getHideFrozen());
                                refresh();
                                toast(prefs.getHideFrozen()
                                        ? "锁住的应用已从桌面移除（入口在最前面）"
                                        : "锁住的应用将显示在桌面上");
                                break;
                            case 4: showHiddenManager(); break;
                            case 5: unfreezeAll(); break;
                            case 6: changeColumns(); break;
                            case 7: refresh(); break;
                            case 8: showWallpaperMenu(); break;
                            case 9: showAbout(); break;
                        }
                    }
                })
                .show();
    }

    /**
     * 系统桌面（GITV）的隐藏入口直达 —— "上帝模式"。
     * 这些 Activity 都带 intent-filter（exported），不校验调用者，可直接拉起：
     *  · CustomDeskActivity          官方导航管理：OK键隐藏/恢复顶部栏目，带"恢复默认"
     *  · ThridPartyAppListActivity   系统桌面的"我的应用"第三方应用列表
     *  · StartUpChoiceActivity       开机进直播 / 开机进主页
     */
    private void showSystemDeskTools() {
        final String[][] comps = new String[][]{
                {"com.gitv.launcher", "com.gitv.launcher.ui.CustomDeskActivity"},
                {"com.gitv.launcher", "com.gitv.launcher.ui.ThridPartyAppListActivity"},
                {"com.gitv.launcher", "com.gitv.launcher.ui.StartUpChoiceActivity"},
        };
        final String[] items = new String[]{
                "桌面导航管理（按OK键隐藏/恢复栏目）",
                "我的应用（系统桌面应用列表）",
                "开机方式选择（直播/主页）",
        };
        new AlertDialog.Builder(this)
                .setTitle("系统桌面工具")
                .setItems(items, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        try {
                            Intent i = new Intent();
                            i.setClassName(comps[which][0], comps[which][1]);
                            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                            startActivity(i);
                        } catch (Throwable t) {
                            toast("打不开：" + t.getMessage());
                        }
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }

    /** 回到系统默认桌面（HOME intent，谁声明了 HOME 谁接手） */
    private void goSystemHome() {
        try {
            Intent home = new Intent(Intent.ACTION_MAIN);
            home.addCategory(Intent.CATEGORY_HOME);
            home.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(home);
        } catch (Throwable t) {
            toast("无法切换：" + t);
        }
    }

    /** 「已锁住」入口：列出所有被冻结的应用，点一个就解冻，最后一项是全部解冻 */
    private void showFrozenVault() {
        if (frozenApps.isEmpty()) {
            toast("没有被锁住的应用");
            return;
        }
        final int n = frozenApps.size();
        final String[] names = new String[n + 1];
        for (int i = 0; i < n; i++) {
            names[i] = frozenApps.get(i).label + "（点击解冻）";
        }
        names[n] = "—— 全部解冻（" + n + " 个）——";

        new AlertDialog.Builder(this)
                .setTitle("已锁住的应用（" + n + "）")
                .setItems(names, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        if (w >= n) {
                            unfreezeAll();
                        } else {
                            final AppEntry target = frozenApps.get(w);
                            new AlertDialog.Builder(LauncherActivity.this)
                                    .setTitle(target.label)
                                    .setMessage("要解冻这个应用吗？\n" + target.pkg)
                                    .setPositiveButton("解冻", new DialogInterface.OnClickListener() {
                                        @Override
                                        public void onClick(DialogInterface dd, int ww) {
                                            doUnfreeze(target);
                                        }
                                    })
                                    .setNegativeButton("取消", null)
                                    .show();
                        }
                    }
                })
                .setNegativeButton("关闭", null)
                .show();
    }

    private void showHiddenManager() {
        final List<String> hidden = prefs.getHidden();
        if (hidden.isEmpty()) {
            toast(getString(R.string.no_hidden));
            return;
        }
        final String[] names = new String[hidden.size()];
        final PackageManager pm = getPackageManager();
        for (int i = 0; i < hidden.size(); i++) {
            String pkg = hidden.get(i);
            try {
                names[i] = pm.getApplicationLabel(pm.getApplicationInfo(pkg, 0)).toString();
            } catch (Throwable t) {
                names[i] = pkg;
            }
        }
        new AlertDialog.Builder(this)
                .setTitle("已隐藏（点击恢复）")
                .setItems(names, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        prefs.removeHidden(hidden.get(w));
                        refresh();
                    }
                })
                .show();
    }

    private void unfreezeAll() {
        new Thread(new Runnable() {
            @Override
            public void run() {
                Set<String> disabled = parseDisabled(RootCmd.listDisabled());
                int n = 0;
                for (String pkg : disabled) {
                    if (RootCmd.unfreeze(pkg)) n++;
                }
                final int count = n;
                handler.post(new Runnable() {
                    @Override
                    public void run() {
                        toast("已解冻 " + count + " 个应用");
                        refresh();
                    }
                });
            }
        }).start();
    }

    private void changeColumns() {
        final String[] opts = new String[]{"5 列", "6 列", "7 列", "8 列"};
        final int[] vals = new int[]{5, 6, 7, 8};
        new AlertDialog.Builder(this)
                .setTitle("每行图标数")
                .setItems(opts, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        prefs.setColumns(vals[w]);
                        grid.setNumColumns(vals[w]);
                        clampSel();
                        applySelection();
                    }
                })
                .show();
    }

    // ---------------------------------------------------------------- 壁纸

    private static final String WALL_DIR = "wallpapers";
    private static final String PREF_WALL = "wallpaper_path";

    private File wallDir() {
        File d = new File(getFilesDir(), WALL_DIR);
        if (!d.exists()) d.mkdirs();
        return d;
    }

    private void showWallpaperMenu() {
        final String[] items = new String[]{
                "从已下载的壁纸里选…",
                "在线获取必应今日壁纸",
                "恢复系统默认壁纸"
        };
        new AlertDialog.Builder(this)
                .setTitle("换壁纸")
                .setItems(items, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        switch (w) {
                            case 0: pickWallpaper(); break;
                            case 1: fetchBingWallpaper(); break;
                            case 2:
                                getSharedPreferences("at4", MODE_PRIVATE).edit()
                                        .remove(PREF_WALL).commit();
                                loadWallpaper();
                                toast("已恢复系统壁纸");
                                break;
                        }
                    }
                })
                .show();
    }

    /** 列出壁纸目录里的图片 */
    private void pickWallpaper() {
        File dir = wallDir();
        File[] fs = dir.listFiles(new FileFilter() {
            @Override
            public boolean accept(File f) {
                String n = f.getName().toLowerCase(Locale.US);
                return n.endsWith(".jpg") || n.endsWith(".jpeg") || n.endsWith(".png");
            }
        });
        if (fs == null || fs.length == 0) {
            toast("壁纸目录是空的：\n" + dir.getAbsolutePath());
            return;
        }
        Arrays.sort(fs, new Comparator<File>() {
            @Override
            public int compare(File a, File b) {
                return a.getName().compareToIgnoreCase(b.getName());
            }
        });
        final File[] list = fs;
        String[] names = new String[list.length];
        for (int i = 0; i < list.length; i++) {
            names[i] = "壁纸 " + (i + 1) + "  （" + (list[i].length() / 1024) + " KB）";
        }
        new AlertDialog.Builder(this)
                .setTitle("换壁纸（共 " + list.length + " 张）")
                .setItems(names, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        applyWallpaper(list[w]);
                    }
                })
                .show();
    }

    private void applyWallpaper(final File f) {
        toast("正在设置壁纸…");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    Bitmap b = BitmapFactory.decodeFile(f.getAbsolutePath());
                    if (b == null) {
                        toastOnUi("图片读不出来（可能不是标准 jpg/png）");
                        return;
                    }
                    WallpaperManager.getInstance(LauncherActivity.this).setBitmap(b);
                    getSharedPreferences("at4", MODE_PRIVATE).edit()
                            .putString(PREF_WALL, f.getAbsolutePath()).commit();
                    final Bitmap fb = b;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            if (wallpaperView != null) wallpaperView.setImageBitmap(fb);
                            toast("壁纸已更换");
                        }
                    });
                } catch (Throwable t) {
                    toastOnUi("设置失败：" + t.getMessage());
                }
            }
        }).start();
    }

    /** 联网抓必应（微软）今日壁纸 */
    private void fetchBingWallpaper() {
        toast("正在下载必应今日壁纸…");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    String api = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN";
                    String json = httpGet(api);
                    String rel = null;
                    int i = json.indexOf("\"url\"");
                    if (i >= 0) {
                        int a = json.indexOf('"', json.indexOf(':', i));
                        int b = json.indexOf('"', a + 1);
                        if (a >= 0 && b > a) rel = json.substring(a + 1, b);
                    }
                    if (rel == null) {
                        toastOnUi("没拿到壁纸地址");
                        return;
                    }
                    if (!rel.startsWith("http")) rel = "https://www.bing.com" + rel;
                    String name = "bing_" + new SimpleDateFormat("yyyyMMdd", Locale.US)
                            .format(new Date()) + ".jpg";
                    File out = new File(wallDir(), name);
                    HttpURLConnection c = (HttpURLConnection) new URL(rel).openConnection();
                    c.setConnectTimeout(10000);
                    c.setReadTimeout(20000);
                    c.setRequestProperty("User-Agent", "AerialTV4");
                    InputStream in = c.getInputStream();
                    FileOutputStream o = new FileOutputStream(out);
                    byte[] buf = new byte[8192];
                    int n;
                    while ((n = in.read(buf)) > 0) o.write(buf, 0, n);
                    o.close();
                    in.close();
                    if (out.length() < 20000) {
                        toastOnUi("下载内容异常，太小了");
                        return;
                    }
                    applyWallpaper(out);
                } catch (Throwable t) {
                    toastOnUi("下载失败：" + t.getMessage());
                }
            }
        }).start();
    }

    private String httpGet(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(15000);
        c.setRequestProperty("User-Agent", "AerialTV4");
        InputStream in = c.getInputStream();
        java.io.ByteArrayOutputStream bo = new java.io.ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
        in.close();
        return new String(bo.toByteArray(), "UTF-8");
    }

    private void toastOnUi(final String msg) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                toast(msg);
            }
        });
    }

    private void showAbout() {
        new AlertDialog.Builder(this)
                .setTitle("Aerial TV 4")
                .setMessage("给 Android 4.4 电视的一块干净桌面。\n\n"
                        + "· 方向键选择，确认键打开\n"
                        + "· 菜单键：锁住后台 / 解冻 / 隐藏 / 卸载 / 桌面设置\n\n"
                        + "免授权冻结（系统应用）：" + (RootCmd.privileged() ? "可用" : "不可用") + "\n"
                        + "su 提权：" + (hasRoot ? "已获取" : "未检测"))
                .setPositiveButton("知道了", null)
                .show();
    }

    // ---------------------------------------------------------------- 杂项

    private void loadWallpaper() {
        // 先试上次自己选的壁纸（系统 WallpaperManager 在部分机器上读不回来）
        try {
            String p = getSharedPreferences("at4", MODE_PRIVATE).getString(PREF_WALL, null);
            if (p != null && new File(p).exists()) {
                Bitmap b = BitmapFactory.decodeFile(p);
                if (b != null && wallpaperView != null) {
                    wallpaperView.setImageBitmap(b);
                    return;
                }
            }
        } catch (Throwable ignored) { }

        try {
            WallpaperManager wm = WallpaperManager.getInstance(this);
            Drawable d = wm.getDrawable();
            if (d != null && wallpaperView != null) {
                wallpaperView.setImageDrawable(d);
            }
        } catch (Throwable ignored) {
            // 拿不到系统壁纸就用渐变背景
        }
    }

    private void updateClock() {
        if (clockView == null) return;
        Date now = new Date();
        clockView.setText(new SimpleDateFormat("HH:mm", Locale.CHINA).format(now));
        if (dateView != null) {
            dateView.setText(new SimpleDateFormat("M月d日 EEEE", Locale.CHINA).format(now));
        }
    }

    private void toast(String msg) {
        Toast.makeText(this, msg, Toast.LENGTH_SHORT).show();
    }
}
