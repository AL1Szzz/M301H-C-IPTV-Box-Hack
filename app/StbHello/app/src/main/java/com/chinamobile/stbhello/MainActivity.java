package com.chinamobile.stbhello;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.widget.LinearLayout;
import android.graphics.Color;
import android.view.Gravity;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout ll = new LinearLayout(this);
        ll.setOrientation(LinearLayout.VERTICAL);
        ll.setBackgroundColor(0xFF101010);
        ll.setGravity(Gravity.CENTER);
        TextView tv = new TextView(this);
        tv.setText("OK 第三方应用可以运行\n\n如果看到这行字，说明盒子没有拦截运行\n\n型号: " + android.os.Build.MODEL
                + "\n系统: Android " + android.os.Build.VERSION.RELEASE
                + "\nSDK: " + android.os.Build.VERSION.SDK_INT);
        tv.setTextColor(Color.WHITE);
        tv.setTextSize(28f);
        tv.setGravity(Gravity.CENTER);
        ll.addView(tv);
        setContentView(ll);
    }
}
