package app.orchard.tv4;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.view.KeyEvent;

/**
 * 盒子上的桌面切换器：
 * 在自带桌面（或其他应用）里按「菜单」键 → 一键切到 AerialTV4；
 * HOME 键保持系统默认（回自带桌面）。
 * AerialTV4 自己在前台时不拦截，菜单键仍归桌面内部功能用。
 */
public class MenuKeyService extends AccessibilityService {

    private static final String TAG = "MenuKeySvc";

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        android.util.Log.w(TAG, "connected, info=" + getServiceInfo());
    }

    @Override
    protected boolean onKeyEvent(KeyEvent event) {
        android.util.Log.w(TAG, "key " + event.getAction() + " code=" + event.getKeyCode()
                + " fg=" + LauncherActivity.sForeground);
        if (event.getAction() == KeyEvent.ACTION_UP
                && event.getKeyCode() == KeyEvent.KEYCODE_MENU
                && !LauncherActivity.sForeground) {
            Intent it = new Intent(this, LauncherActivity.class);
            it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                    | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
            try {
                startActivity(it);
                android.util.Log.w(TAG, "launch ok");
            } catch (Throwable t) {
                android.util.Log.w(TAG, "launch fail " + t);
            }
            return true;
        }
        return false;
    }

    @Override
    public void onAccessibilityEvent(android.view.accessibility.AccessibilityEvent event) {
    }

    @Override
    public void onInterrupt() {
    }
}
