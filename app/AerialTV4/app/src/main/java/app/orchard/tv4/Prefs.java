package app.orchard.tv4;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** 桌面自身的小设置：隐藏列表、每行列数 */
public final class Prefs {
    private static final String NAME = "aerial_tv4";
    private static final String KEY_HIDDEN = "hidden";
    private static final String KEY_COLUMNS = "columns";
    private static final String KEY_HIDE_FROZEN = "hide_frozen";
    private static final String SEP = "\u0001";

    private final SharedPreferences sp;

    public Prefs(Context c) {
        sp = c.getSharedPreferences(NAME, Context.MODE_PRIVATE);
    }

    public List<String> getHidden() {
        String raw = sp.getString(KEY_HIDDEN, "");
        if (raw == null || raw.length() == 0) return new ArrayList<String>();
        return new ArrayList<String>(Arrays.asList(raw.split(SEP)));
    }

    public void setHidden(List<String> list) {
        StringBuilder sb = new StringBuilder();
        for (String s : list) {
            if (sb.length() > 0) sb.append(SEP);
            sb.append(s);
        }
        sp.edit().putString(KEY_HIDDEN, sb.toString()).commit();
    }

    public void addHidden(String pkg) {
        List<String> l = getHidden();
        if (!l.contains(pkg)) {
            l.add(pkg);
            setHidden(l);
        }
    }

    public void removeHidden(String pkg) {
        List<String> l = getHidden();
        l.remove(pkg);
        setHidden(l);
    }

    public int getColumns() {
        return sp.getInt(KEY_COLUMNS, 6);
    }

    public void setColumns(int n) {
        sp.edit().putInt(KEY_COLUMNS, n).commit();
    }

    /** 被冻结（锁住）的应用是否从桌面网格里移除，改由「已锁住」入口统一管理。默认移除。 */
    public boolean getHideFrozen() {
        return sp.getBoolean(KEY_HIDE_FROZEN, true);
    }

    public void setHideFrozen(boolean b) {
        sp.edit().putBoolean(KEY_HIDE_FROZEN, b).commit();
    }
}
