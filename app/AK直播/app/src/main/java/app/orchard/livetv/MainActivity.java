package app.orchard.livetv;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.text.InputType;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.VideoView;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;

/** AK直播：内置频道 + 遥控器优化 + 设置面板，全部使用 API 19 可用接口 */
public class MainActivity extends Activity {

    // ---- 视图 ----
    private VideoView video;
    private LinearLayout panel;      // 左侧频道面板
    private LinearLayout setPanel;   // 设置面板
    private ListView chList;
    private ListView setList;
    private TextView groupName;
    private TextView status;

    // ---- 数据 ----
    private List<Chan> all = new ArrayList<Chan>();
    private List<Chan> shown = new ArrayList<Chan>();
    private List<String> groups = new ArrayList<String>();
    private int groupIdx = 0;
    private int sel = 0;          // 当前分组内的选中下标
    private int target = -1;      // 防抖播放目标
    private int errCount = 0;     // 连续失败次数，防止无限跳台

    private Handler handler = new Handler();
    private SharedPreferences prefs;
    private List<Setting> settings = new ArrayList<Setting>();
    private SetAdapter setAdapter;

    // 频道源：内置 / 自定义
    private static final String SRC_BUILTIN = "内置频道";
    private String customUrl = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences("livetv", MODE_PRIVATE);

        video = (VideoView) findViewById(R.id.video);
        panel = (LinearLayout) findViewById(R.id.panel);
        setPanel = (LinearLayout) findViewById(R.id.setpanel);
        chList = (ListView) findViewById(R.id.chlist);
        setList = (ListView) findViewById(R.id.setlist);
        groupName = (TextView) findViewById(R.id.group_name);
        status = (TextView) findViewById(R.id.status);

        buildSettings();
        setAdapter = new SetAdapter();
        setList.setAdapter(setAdapter);

        video.setOnPreparedListener(new MediaPlayer.OnPreparedListener() {
            public void onPrepared(MediaPlayer mp) {
                errCount = 0;
                mp.setScreenOnWhilePlaying(true);
                applyScale(mp.getVideoWidth(), mp.getVideoHeight());
                Chan c = cur();
                showStatus("正在播放：" + (c != null ? c.name : ""));
            }
        });
        video.setOnErrorListener(new MediaPlayer.OnErrorListener() {
            public boolean onError(MediaPlayer mp, int what, int extra) {
                Chan c = cur();
                showStatus("× " + (c != null ? c.name : "") + " 无法播放（" + what + "）");
                if (prefs.getBoolean("autoskip", true)) {
                    errCount++;
                    if (errCount <= 5) {
                        showStatus("× " + (c != null ? c.name : "") + " 失效，自动换下一个…");
                        handler.postDelayed(new Runnable() {
                            public void run() {
                                step(1);
                            }
                        }, 1500);
                    }
                }
                return true;
            }
        });

        chList.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onItemSelected(AdapterView<?> p, View v, int pos, long id) {
                sel = pos;
                schedulePlay(pos);
            }
            public void onNothingSelected(AdapterView<?> p) {
            }
        });
        chList.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            public void onItemClick(AdapterView<?> p, View v, int pos, long id) {
                sel = pos;
                play(pos);
                hidePanel();
            }
        });

        loadSource();
    }

    // ==================== 频道源 ====================

    private void loadSource() {
        if (SRC_BUILTIN.equals(prefs.getString("source", SRC_BUILTIN))) {
            parse(loadAssetText());
        } else {
            String saved = readCustom();
            if (saved != null && saved.length() > 0) {
                parse(saved);
            } else {
                parse(loadAssetText());
            }
        }
        buildGroups();
        showGroup(0);
        if (prefs.getBoolean("panel", true)) {
            showPanel();
        } else {
            hidePanel();
            if (prefs.getBoolean("autoplay", true)) play(0);
        }
    }

    private String loadAssetText() {
        try {
            InputStream in = getAssets().open("live.m3u");
            return readAll(new InputStreamReader(in, "UTF-8"));
        } catch (Exception e) {
            return "";
        }
    }

    private String readCustom() {
        try {
            File f = new File(getFilesDir(), "custom.m3u");
            if (!f.exists()) return null;
            return readAll(new InputStreamReader(new FileInputStream(f), "UTF-8"));
        } catch (Exception e) {
            return null;
        }
    }

    private void saveCustom(String text) {
        try {
            FileOutputStream o = new FileOutputStream(new File(getFilesDir(), "custom.m3u"));
            o.write(text.getBytes("UTF-8"));
            o.close();
        } catch (Exception e) {
        }
    }

    private String readAll(InputStreamReader r) throws Exception {
        BufferedReader b = new BufferedReader(r);
        StringBuilder s = new StringBuilder();
        String line;
        while ((line = b.readLine()) != null) {
            s.append(line).append('\n');
        }
        b.close();
        return s.toString();
    }

    private void parse(String text) {
        all.clear();
        if (text == null) return;
        String[] lines = text.split("\n");
        String name = null;
        for (String l : lines) {
            l = l.trim();
            if (l.startsWith("#EXTINF")) {
                int i = l.indexOf(',');
                name = (i >= 0) ? l.substring(i + 1).trim() : "未命名";
                if (name.length() == 0) name = "未命名";
            } else if (l.startsWith("http")) {
                String g = "频道";
                int gi = l.indexOf("group-title=");
                all.add(new Chan(name == null ? ("频道" + (all.size() + 1)) : name, l, g));
                name = null;
            }
        }
        // 从 #EXTINF 里取分组（上面简化处理，这里再补一次精确解析）
        name = null;
        int idx = -1;
        for (String l : lines) {
            l = l.trim();
            if (l.startsWith("#EXTINF")) {
                int i = l.indexOf(',');
                name = (i >= 0) ? l.substring(i + 1).trim() : "未命名";
                int g1 = l.indexOf("group-title=\"");
                if (g1 >= 0) {
                    int g2 = l.indexOf('"', g1 + 13);
                    if (g2 > g1) name = name + ""; // 保留显示名
                    idx = -1;
                    // 记录分组供下一条 URL 使用
                }
            } else if (l.startsWith("http")) {
                idx++;
                if (idx < all.size()) {
                    int g1 = l.indexOf("group-title=");
                    // 分组在上一行 EXTINF 中，回溯解析
                }
            }
        }
        // 精确解析分组：重新走一遍
        parseGroups(text);
    }

    private void parseGroups(String text) {
        String[] lines = text.split("\n");
        int idx = -1;
        String name = null;
        String grp = null;
        for (String l : lines) {
            l = l.trim();
            if (l.startsWith("#EXTINF")) {
                int i = l.indexOf(',');
                name = (i >= 0) ? l.substring(i + 1).trim() : "未命名";
                int g1 = l.indexOf("group-title=\"");
                grp = null;
                if (g1 >= 0) {
                    int g2 = l.indexOf('"', g1 + 13);
                    if (g2 > g1) grp = l.substring(g1 + 13, g2);
                }
            } else if (l.startsWith("http")) {
                idx++;
                if (idx < all.size()) {
                    all.get(idx).name = (name == null ? all.get(idx).name : name);
                    all.get(idx).group = (grp == null ? "频道" : grp);
                }
                name = null;
                grp = null;
            }
        }
    }

    // ==================== 分组 ====================

    private void buildGroups() {
        groups.clear();
        LinkedHashSet<String> s = new LinkedHashSet<String>();
        for (Chan c : all) s.add(c.group);
        groups.addAll(s);
        if (groups.size() == 0) groups.add("频道");
    }

    private void showGroup(int i) {
        if (groups.size() == 0) return;
        groupIdx = ((i % groups.size()) + groups.size()) % groups.size();
        String g = groups.get(groupIdx);
        shown.clear();
        for (Chan c : all) {
            if (g.equals(c.group)) shown.add(c);
        }
        List<String> names = new ArrayList<String>();
        for (Chan c : shown) names.add(c.name);
        chList.setAdapter(new ArrayAdapter<String>(this, R.layout.item_channel, R.id.chan_name, names));
        groupName.setText(g + "（" + shown.size() + "台）  ◀ ▶ 换分组");
        sel = 0;
        if (shown.size() > 0) {
            chList.setSelection(0);
        }
    }

    // ==================== 播放 ====================

    private Chan cur() {
        if (sel >= 0 && sel < shown.size()) return shown.get(sel);
        return null;
    }

    private void schedulePlay(int pos) {
        target = pos;
        handler.removeCallbacks(playTask);
        handler.postDelayed(playTask, delay());
    }

    private int delay() {
        int d = prefs.getInt("delay", 1);
        if (d == 0) return 300;
        if (d == 2) return 1500;
        return 700;
    }

    private Runnable playTask = new Runnable() {
        public void run() {
            if (target >= 0 && target < shown.size()) play(target);
        }
    };

    private void play(int pos) {
        if (pos < 0 || pos >= shown.size()) return;
        sel = pos;
        Chan c = shown.get(pos);
        showStatus("加载中：" + c.name);
        try {
            video.stopPlayback();
            video.setVideoURI(Uri.parse(c.url));
            video.start();
        } catch (Exception e) {
            showStatus("打开失败：" + e.getMessage());
        }
    }

    /** 换台：dir=1 下一个，-1 上一个 */
    private void step(int dir) {
        if (shown.size() == 0) return;
        int n = sel + dir;
        if (n < 0) n = shown.size() - 1;
        if (n >= shown.size()) n = 0;
        sel = n;
        chList.setSelection(n);
        play(n);
    }

    private void applyScale(int vw, int vh) {
        if (vw <= 0 || vh <= 0) return;
        int sw = getResources().getDisplayMetrics().widthPixels;
        int sh = getResources().getDisplayMetrics().heightPixels;
        FrameLayout.LayoutParams lp = (FrameLayout.LayoutParams) video.getLayoutParams();
        if (prefs.getInt("scale", 0) == 1) {
            // 原始比例：按视频宽高比适配屏幕
            float vr = (float) vw / vh;
            float sr = (float) sw / sh;
            if (vr > sr) {
                lp.width = sw;
                lp.height = (int) (sw / vr);
            } else {
                lp.height = sh;
                lp.width = (int) (sh * vr);
            }
        } else {
            lp.width = ViewGroup.LayoutParams.MATCH_PARENT;
            lp.height = ViewGroup.LayoutParams.MATCH_PARENT;
        }
        lp.gravity = android.view.Gravity.CENTER;
        video.setLayoutParams(lp);
    }

    // ==================== 面板 ====================

    private void showPanel() {
        panel.setVisibility(View.VISIBLE);
        chList.requestFocus();
    }

    private void hidePanel() {
        panel.setVisibility(View.GONE);
        video.requestFocus();
    }

    private boolean panelVisible() {
        return panel.getVisibility() == View.VISIBLE;
    }

    // ==================== 设置 ====================

    private void buildSettings() {
        settings.clear();
        settings.add(new Setting("source", "频道源", new String[]{SRC_BUILTIN, "自定义源"}, 0, true));
        settings.add(new Setting("custom", "自定义源地址", null, 0, false)); // 动作项
        settings.add(new Setting("autoskip", "失效频道自动跳过", new String[]{"开", "关"}, 0, false));
        settings.add(new Setting("autoplay", "启动即播放", new String[]{"开", "关"}, 0, false));
        settings.add(new Setting("panel", "启动显示频道列表", new String[]{"开", "关"}, 0, false));
        settings.add(new Setting("delay", "换台延迟", new String[]{"0.3秒", "0.7秒", "1.5秒"}, 1, false));
        settings.add(new Setting("scale", "画面缩放", new String[]{"全屏拉伸", "原始比例"}, 0, false));
        settings.add(new Setting("status", "显示状态提示", new String[]{"开", "关"}, 0, false));
        settings.add(new Setting("about", "版本", new String[]{"AK直播 1.1"}, 0, false));

        // 从 prefs 还原
        for (Setting s : settings) {
            if ("source".equals(s.key)) {
                s.idx = SRC_BUILTIN.equals(prefs.getString("source", SRC_BUILTIN)) ? 0 : 1;
            } else if ("custom".equals(s.key)) {
                s.value = prefs.getString("customUrl", "未设置");
            } else if ("about".equals(s.key)) {
                // 只读
            } else if ("status".equals(s.key)) {
                s.idx = prefs.getBoolean("status", true) ? 0 : 1;
            } else if ("scale".equals(s.key)) {
                s.idx = prefs.getInt("scale", 0);
            } else if ("delay".equals(s.key)) {
                s.idx = prefs.getInt("delay", 1);
            } else {
                s.idx = prefs.getBoolean(s.key, true) ? 0 : 1;
            }
        }
        customUrl = prefs.getString("customUrl", "");
    }

    private void openSettings() {
        setPanel.setVisibility(View.VISIBLE);
        setAdapter.notifyDataSetChanged();
        setList.setSelection(0);
        setList.requestFocus();
    }

    private void closeSettings() {
        setPanel.setVisibility(View.GONE);
        if (panelVisible()) chList.requestFocus();
        else video.requestFocus();
    }

    private boolean settingsVisible() {
        return setPanel.getVisibility() == View.VISIBLE;
    }

    /** 设置项左右键改值 */
    private void changeSetting(int dir) {
        int pos = setList.getSelectedItemPosition();
        if (pos < 0 || pos >= settings.size()) return;
        Setting s = settings.get(pos);
        if (s.opts == null || s.opts.length <= 1) return;
        s.idx = (s.idx + dir + s.opts.length) % s.opts.length;
        saveSetting(s);
        setAdapter.notifyDataSetChanged();
        applySetting(s);
    }

    private void saveSetting(Setting s) {
        SharedPreferences.Editor e = prefs.edit();
        if ("source".equals(s.key)) {
            e.putString("source", s.opts[s.idx]);
        } else if ("status".equals(s.key)) {
            e.putBoolean("status", s.idx == 0);
        } else if ("scale".equals(s.key)) {
            e.putInt("scale", s.idx);
        } else if ("delay".equals(s.key)) {
            e.putInt("delay", s.idx);
        } else if (s.opts != null && s.opts.length == 2 && "开".equals(s.opts[0])) {
            e.putBoolean(s.key, s.idx == 0);
        }
        e.commit();
    }

    private void applySetting(Setting s) {
        if ("scale".equals(s.key)) {
            // 重新应用（需要当前视频尺寸，简单起见重播一次当前频道）
            if (sel >= 0 && sel < shown.size()) play(sel);
        } else if ("status".equals(s.key)) {
            if (s.idx == 1) status.setVisibility(View.GONE);
            else status.setVisibility(View.VISIBLE);
        } else if ("source".equals(s.key)) {
            if (s.idx == 0) {
                parse(loadAssetText());
                buildGroups();
                showGroup(0);
            } else if (customUrl.length() > 0) {
                fetchCustom(customUrl);
            }
        }
    }

    private void triggerSetting(int pos) {
        if (pos < 0 || pos >= settings.size()) return;
        Setting s = settings.get(pos);
        if ("custom".equals(s.key)) {
            showUrlDialog();
        }
    }

    private void showUrlDialog() {
        final EditText input = new EditText(this);
        input.setText(customUrl);
        input.setSingleLine(true);
        input.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        new AlertDialog.Builder(this)
                .setTitle("自定义直播源地址")
                .setMessage("输入 m3u / txt 直播源的 http 地址")
                .setView(input)
                .setPositiveButton("下载并使用", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface d, int w) {
                        String u = input.getText().toString().trim();
                        if (u.length() > 0) {
                            customUrl = u;
                            prefs.edit().putString("customUrl", u).commit();
                            settings.get(1).value = u;
                            setAdapter.notifyDataSetChanged();
                            fetchCustom(u);
                        }
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }

    private void fetchCustom(final String url) {
        showStatus("正在下载频道源…");
        new Thread(new Runnable() {
            public void run() {
                String text = null;
                try {
                    HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
                    c.setConnectTimeout(10000);
                    c.setReadTimeout(15000);
                    c.setRequestProperty("User-Agent", "AKLiveTV");
                    InputStream in = c.getInputStream();
                    ByteArrayOutputStream bo = new ByteArrayOutputStream();
                    byte[] buf = new byte[8192];
                    int n;
                    while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
                    in.close();
                    text = new String(bo.toByteArray(), "UTF-8");
                } catch (Exception e) {
                    final String err = e.getMessage();
                    runOnUiThread(new Runnable() {
                        public void run() {
                            showStatus("下载失败：" + err);
                        }
                    });
                    return;
                }
                final String t = text;
                runOnUiThread(new Runnable() {
                    public void run() {
                        saveCustom(t);
                        parse(t);
                        buildGroups();
                        showGroup(0);
                        prefs.edit().putString("source", "自定义源").commit();
                        showStatus("频道源已更新，共 " + all.size() + " 台");
                        showPanel();
                        if (shown.size() > 0) play(0);
                    }
                });
            }
        }).start();
    }

    // ==================== 状态 ====================

    private Runnable hideStatus = new Runnable() {
        public void run() {
            status.setVisibility(View.GONE);
        }
    };

    private void showStatus(String s) {
        if (!prefs.getBoolean("status", true)) {
            status.setVisibility(View.GONE);
            return;
        }
        status.setVisibility(View.VISIBLE);
        status.setText(s);
        handler.removeCallbacks(hideStatus);
        handler.postDelayed(hideStatus, 4000);
    }

    // ==================== 遥控器 ====================

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        boolean settingsOpen = settingsVisible();

        // ---- 设置面板打开时 ----
        if (settingsOpen) {
            switch (keyCode) {
                case KeyEvent.KEYCODE_DPAD_LEFT:
                    changeSetting(-1);
                    return true;
                case KeyEvent.KEYCODE_DPAD_RIGHT:
                    changeSetting(1);
                    return true;
                case KeyEvent.KEYCODE_DPAD_CENTER:
                case KeyEvent.KEYCODE_ENTER:
                    triggerSetting(setList.getSelectedItemPosition());
                    return true;
                case KeyEvent.KEYCODE_BACK:
                case KeyEvent.KEYCODE_MENU:
                    closeSettings();
                    return true;
            }
            return super.onKeyDown(keyCode, event);
        }

        switch (keyCode) {
            case KeyEvent.KEYCODE_MENU:
            case KeyEvent.KEYCODE_SETTINGS:
                openSettings();
                return true;

            case KeyEvent.KEYCODE_DPAD_UP:
                if (!panelVisible()) step(-1);
                return super.onKeyDown(keyCode, event);

            case KeyEvent.KEYCODE_DPAD_DOWN:
                if (!panelVisible()) step(1);
                return super.onKeyDown(keyCode, event);

            case KeyEvent.KEYCODE_DPAD_LEFT:
                if (panelVisible()) {
                    hidePanel();              // 收起列表，全屏看
                } else {
                    showGroup(groupIdx - 1);  // 全屏时左键换上一分组
                    showStatus("分组：" + groups.get(groupIdx));
                    if (prefs.getBoolean("autoplay", true) && shown.size() > 0) play(0);
                }
                return true;

            case KeyEvent.KEYCODE_DPAD_RIGHT:
                if (panelVisible()) {
                    showGroup(groupIdx + 1);  // 列表展开时右键换分组
                    showStatus("分组：" + groups.get(groupIdx));
                } else {
                    showGroup(groupIdx + 1);
                    showStatus("分组：" + groups.get(groupIdx));
                    if (prefs.getBoolean("autoplay", true) && shown.size() > 0) play(0);
                }
                return true;

            case KeyEvent.KEYCODE_DPAD_CENTER:
            case KeyEvent.KEYCODE_ENTER:
                if (panelVisible()) {
                    play(sel);
                    hidePanel();
                } else {
                    showPanel();
                }
                return true;

            case KeyEvent.KEYCODE_BACK:
                if (panelVisible()) {
                    finish();
                    return true;
                } else {
                    showPanel();
                    return true;
                }

            case KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE:
                if (video.isPlaying()) video.pause();
                else video.start();
                return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacks(playTask);
        handler.removeCallbacks(hideStatus);
        super.onDestroy();
    }

    // ==================== 内部类 ====================

    static class Chan {
        String name, url, group;
        Chan(String n, String u, String g) { name = n; url = u; group = g; }
    }

    static class Setting {
        String key, label;
        String[] opts;
        int idx;
        boolean isSource;
        String value;   // 动作项显示用
        Setting(String k, String l, String[] o, int i, boolean src) {
            key = k; label = l; opts = o; idx = i; isSource = src;
        }
    }

    class SetAdapter extends BaseAdapter {
        public int getCount() { return settings.size(); }
        public Object getItem(int p) { return settings.get(p); }
        public long getItemId(int p) { return p; }

        public View getView(int p, View cv, ViewGroup parent) {
            View v = cv;
            if (v == null) {
                v = LayoutInflater.from(MainActivity.this).inflate(R.layout.item_setting, parent, false);
            }
            Setting s = settings.get(p);
            TextView l = (TextView) v.findViewById(R.id.set_label);
            TextView val = (TextView) v.findViewById(R.id.set_value);
            l.setText(s.label);
            if (s.opts == null) {
                val.setText(s.value == null ? "点击输入" : s.value);
            } else {
                val.setText(s.opts[s.idx]);
            }
            return v;
        }
    }
}
