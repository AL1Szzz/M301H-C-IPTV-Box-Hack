package app.orchard.tv4;

import android.content.Context;
import android.content.pm.PackageManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.TextView;

import java.util.List;

public class AppAdapter extends BaseAdapter {
    private final Context ctx;
    private final List<AppEntry> items;
    private int sel = 0;

    public AppAdapter(Context ctx, List<AppEntry> items) {
        this.ctx = ctx;
        this.items = items;
    }

    public void setSelection(int pos) {
        this.sel = pos;
    }

    public int getSelection() {
        return sel;
    }

    @Override
    public int getCount() {
        return items.size();
    }

    @Override
    public Object getItem(int position) {
        return items.get(position);
    }

    @Override
    public long getItemId(int position) {
        return position;
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        ViewHolder h;
        if (convertView == null) {
            convertView = LayoutInflater.from(ctx).inflate(R.layout.item_app, parent, false);
            h = new ViewHolder();
            h.root = convertView;
            h.icon = (ImageView) convertView.findViewById(R.id.icon);
            h.label = (TextView) convertView.findViewById(R.id.label);
            h.badge = (ImageView) convertView.findViewById(R.id.frozenBadge);
            convertView.setTag(h);
        } else {
            h = (ViewHolder) convertView.getTag();
        }

        AppEntry e = items.get(position);
        if (e.icon != null) {
            h.icon.setImageDrawable(e.icon);
        } else {
            PackageManager pm = ctx.getPackageManager();
            try {
                h.icon.setImageDrawable(pm.getApplicationIcon(e.pkg));
            } catch (Throwable t) {
                h.icon.setImageResource(R.drawable.ic_launcher);
            }
        }
        h.label.setText(e.label);
        h.badge.setVisibility(e.frozen ? View.VISIBLE : View.GONE);
        decorate(convertView, position == sel, e.frozen);
        return convertView;
    }

    /** 选中态的视觉反馈：描边底板 + 图标放大 + 文字提亮。冻结的额外降透明度。 */
    static void decorate(View v, boolean selected, boolean frozen) {
        if (v == null) return;
        v.setBackgroundResource(selected ? R.drawable.item_selected : R.drawable.item_normal);

        View icon = v.findViewById(R.id.icon);
        if (icon != null) {
            float s = selected ? 1.18f : 1.0f;
            icon.setScaleX(s);
            icon.setScaleY(s);
            icon.setAlpha(frozen ? (selected ? 150 : 110) : 255);
        }

        View label = v.findViewById(R.id.label);
        if (label instanceof TextView) {
            TextView tv = (TextView) label;
            if (selected) {
                tv.setTextColor(0xFFFFFFFF);
                tv.getPaint().setFakeBoldText(true);
                tv.setAlpha(1f);
            } else {
                tv.setTextColor(frozen ? 0xFF8FA0B8 : 0xFFE4EBF7);
                tv.getPaint().setFakeBoldText(false);
                tv.setAlpha(0.95f);
            }
        }
    }

    static class ViewHolder {
        View root;
        ImageView icon;
        TextView label;
        ImageView badge;
    }
}
