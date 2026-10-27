package com.projectinfinity.kodi;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

/**
 * Add one read-only bottom version label without modifying, hiding, moving,
 * or repurposing ANY of the original chooser views, including the HM caption.
 * Only this new view's bounds are updated after the Stage's original layout.
 */
public final class ChooserReleaseFooter implements View.OnLayoutChangeListener {
    private static final String TAG = "chooser-app-version";
    private final TextView label;
    private final ViewGroup parent;

    private ChooserReleaseFooter(ViewGroup parent, boolean light) {
        this.parent = parent;
        Context context = parent.getContext();
        label = new TextView(context);
        label.setTag(TAG);
        label.setText(installedVersion(context));
        label.setTextColor(light ? 0xff071a30 : 0xffdbe6fa);
        label.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        label.setTextSize(TypedValue.COMPLEX_UNIT_PX, dp(context, 9));
        label.setGravity(Gravity.CENTER);
        label.setIncludeFontPadding(false);
        label.setSingleLine(true);
        label.setFocusable(false);
        label.setClickable(false);
        parent.addView(label);
        parent.addOnLayoutChangeListener(this);
    }

    public static void install(ViewGroup parent, boolean light) {
        if (parent.findViewWithTag(TAG) == null) new ChooserReleaseFooter(parent, light);
    }

    private static String installedVersion(Context context) {
        try {
            PackageInfo info = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
            return "App version " + info.versionCode;
        } catch (PackageManager.NameNotFoundException unavailable) {
            return "App version unavailable";
        }
    }

    private static int dp(Context c, float value) {
        return Math.round(value * c.getResources().getDisplayMetrics().density);
    }

    @Override public void onLayoutChange(View v, int l, int t, int r, int b,
            int oldL, int oldT, int oldR, int oldB) {
        int windowW = Math.max(1, r - l);
        int windowH = Math.max(1, b - t);
        Context c = parent.getContext();
        int margin = dp(c, 24);
        int textW = Math.max(1, windowW - margin * 2);
        int textH = Math.max(dp(c, 11), Math.round(label.getPaint().getFontSpacing()));
        label.measure(View.MeasureSpec.makeMeasureSpec(textW, View.MeasureSpec.EXACTLY),
                      View.MeasureSpec.makeMeasureSpec(textH, View.MeasureSpec.EXACTLY));
        int x = (windowW - textW) / 2;
        // Original slogans and their measured/layout coordinates stay unchanged.
        // Their lower baseline ends at stage-height - 14dp; this new line is below.
        int y = Math.max(0, windowH - textH - dp(c, 1));
        label.layout(x, y, x + textW, y + textH);
    }
}
