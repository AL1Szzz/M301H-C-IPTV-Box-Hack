package app.orchard.tv4;

import android.graphics.drawable.Drawable;

/** 网格里的一个应用 */
public class AppEntry {
    public final String pkg;
    public String label;
    public Drawable icon;
    public boolean frozen;   // 已被冻结（锁后台）
    public boolean system;   // 系统应用
    public boolean vault;    // 这是「已锁住的应用」管理入口，不是一个真正的应用

    public AppEntry(String pkg, String label, Drawable icon, boolean system) {
        this.pkg = pkg;
        this.label = label;
        this.icon = icon;
        this.system = system;
    }
}
