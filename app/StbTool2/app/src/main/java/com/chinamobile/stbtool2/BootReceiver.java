package com.chinamobile.stbtool2;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        String a = i == null ? "" : i.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(a)
                || "android.intent.action.USER_PRESENT".equals(a)
                || "android.net.conn.CONNECTIVITY_CHANGE".equals(a)) {
            try { c.startService(new Intent(c, HttpService.class)); }
            catch (Throwable ignored) { }
        }
    }
}
