package com.chinamobile.stbtool2;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF101018);
        ScrollView sv = new ScrollView(this);
        TextView tv = new TextView(this);
        tv.setTextColor(0xFFE8E8E8);
        tv.setTextSize(16f);
        tv.setPadding(24, 24, 24, 24);
        tv.setMovementMethod(ScrollingMovementMethod.getInstance());
        tv.setText("系统助手 v4\n\n"
                + "HTTP 服务跑在后台服务里（界面退出也不会停）\n\n"
                + "电脑浏览器打开：\n"
                + "  http://192.168.50.52:9998/\n\n"
                + "  /shot.jpg   单张截图\n"
                + "  /stream     实时画面(MJPEG)\n"
                + "  /cmd        远程命令\n"
                + "  /key?code=  模拟按键\n\n"
                + "后台正在尝试开启 ADB，稍后刷新 /log 查看。");
        sv.addView(tv, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(sv, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        setContentView(root);

        startService(new Intent(this, HttpService.class));
    }
}
