package com.projectinfinity.kodi;

import android.app.Activity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.BaseAdapter;
import android.widget.GridView;
import android.widget.LinearLayout;
import android.widget.ListView;

/** Approved expanded Pro composition. Original controls, rows and playback remain owned by Pro. */
public final class CobraProExpandedLayout {
    private CobraProExpandedLayout() {}

    private static Object field(Activity owner, String name) {
        return CobraArrange.ownedField(owner, name);
    }

    private static int dimension(Object layout, String name) {
        if (layout == null) return 0;
        try {
            java.lang.reflect.Field f = layout.getClass().getDeclaredField(name);
            f.setAccessible(true);
            return f.getInt(layout);
        } catch (ReflectiveOperationException error) {
            throw new IllegalStateException("Pro layout contract: " + name, error);
        }
    }

    private static boolean pro(Activity owner) {
        return "focus".equals(field(owner, "mCobraGuideStyle"))
            && Boolean.TRUE.equals(field(owner, "mCobraProActive"))
            && !Boolean.TRUE.equals(field(owner, "mCobraProSportsActive"));
    }

    private static boolean expanded(Activity owner, Object layout) {
        // Usable native layout dimensions, not display pixels or drawer animation bounds.
        // The narrow cover, cover landscape and small windows keep their original path.
        return pro(owner) && dimension(layout, "width") >= 700
            && dimension(layout, "height") >= 600;
    }

    public static int[][] layout(Activity owner, int[][] original, Object model) {
        if (expanded(owner, model)) {
            int width = dimension(model, "width"), height = dimension(model, "height");
            int top = original[0][1] + original[0][3] + 8;
            int available = Math.max(0, height - top);
            int body = width - 16, gap = 8;
            boolean information = original[2][3] > 0;
            int player = information ? Math.round((body - gap) * .59f) : body;
            // Keep space for the existing navigation and channel rows. The unchanged
            // native video-size policy fits the video within this frame, without stretching.
            int panel = Math.min(Math.round(player * 9f / 16f), Math.round(available * .42f));
            float font = Math.max(1f, Math.min(2f, owner.getResources().getConfiguration().fontScale));
            panel = Math.max(Math.round(122f + (font - 1f) * 65f), panel);
            panel = Math.min(panel, Math.max(0, available - 8));
            original[1] = new int[]{8, top, player, panel};
            original[2] = information ? new int[]{8 + player + gap, top, body - player - gap, panel}
                : new int[]{0, 0, 0, 0};
            original[3] = new int[]{8, top + panel + 8, body, Math.max(0, available - panel - 8)};
        }
        // Native viewport/configuration callbacks rebuild the browser immediately
        // after layout. Convert only at the end of that existing render, so its
        // scroll snapshot never reads an unmeasured intermediate replacement list.
        return original;
    }

    public static void sync(Activity owner) {
        if (!pro(owner)) return;
        Object object = field(owner, "mCobraGuideList");
        Object parent = field(owner, "mCobraGuideBrowser");
        if (!(object instanceof AbsListView) || !(parent instanceof LinearLayout)) return;
        AbsListView old = (AbsListView)object;
        if (!"pro_channel_list".equals(old.getTag()) || old.getParent() != parent) return;
        boolean two = expanded(owner, field(owner, "mCobraModeLayout"));
        if (two == (old instanceof Channels)) return;
        if (!(old.getAdapter() instanceof BaseAdapter)) return;
        BaseAdapter adapter = (BaseAdapter)old.getAdapter();
        int first = old.getFirstVisiblePosition();
        View leading = old.getChildAt(0);
        int offset = leading == null ? 0 : leading.getTop() - old.getPaddingTop();
        int selected = old.getSelectedItemPosition();
        View focused = old.findFocus();
        int focusPosition = focused == null ? -1 : old.getPositionForView(focused);
        CharSequence focusLabel = focused == null ? null : focused.getContentDescription();
        boolean hadFocus = old.hasFocus();
        AbsListView next;
        if (two) {
            next = new Channels(owner);
        } else {
            ListView list = new ListView(owner);
            list.setItemsCanFocus(true);
            next = list;
        }
        next.setTag("pro_channel_list");
        LinearLayout browser = (LinearLayout)parent;
        browser.removeView(old);
        old.setAdapter(null);
        CobraArrange.ownedCall(owner, "cobraInstallModeList",
            new Class<?>[]{LinearLayout.class, AbsListView.class, BaseAdapter.class}, browser, next, adapter);
        if (next instanceof ListView) ((ListView)next).setItemsCanFocus(true);
        int pad = Math.round(8 * owner.getResources().getDisplayMetrics().density);
        next.setPadding(0, pad, 0, pad);
        next.setClipToPadding(true);
        // Positions are native channel positions in both widgets. No paired adapter,
        // copied channel data or changed provider/EPG indexing is introduced.
        next.setSelectionFromTop(Math.max(0, first), offset);
        if (hadFocus) next.addOnLayoutChangeListener(new Focus(focusPosition >= 0 ? focusPosition : selected, focusLabel));
    }

    public static void restoreSelection(AbsListView list, int position, int offset) {
        if (list instanceof Channels) list.setSelectionFromTop(position, offset);
        else list.setSelection(position);
    }

    public static boolean rowWide(View row, boolean original) {
        return !(row.getParent() instanceof Channels) && original;
    }

    public static int rowHeight(View row, int original) {
        if (!(row.getParent() instanceof Channels)) return original;
        float scale = row.getResources().getDisplayMetrics().density;
        float font = Math.max(1f, row.getResources().getConfiguration().fontScale);
        return Math.round((90f + (font - 1f) * 45f) * scale);
    }

    private static final class Channels extends GridView {
        Channels(Activity owner) {
            super(owner);
            setNumColumns(2);
            setStretchMode(GridView.STRETCH_COLUMN_WIDTH);
            setHorizontalSpacing(Math.round(8 * getResources().getDisplayMetrics().density));
            setVerticalSpacing(Math.round(4 * getResources().getDisplayMetrics().density));
            setDescendantFocusability(ViewGroup.FOCUS_AFTER_DESCENDANTS);
        }
    }

    private static final class Focus implements View.OnLayoutChangeListener {
        private final int position;
        private final CharSequence label;
        Focus(int position, CharSequence label) { this.position = position; this.label = label; }
        public void onLayoutChange(View view, int l, int t, int r, int b, int ol, int ot, int or, int ob) {
            AbsListView list = (AbsListView)view;
            if (list.getChildCount() == 0) return;
            list.removeOnLayoutChangeListener(this);
            View row = list.getChildAt(position - list.getFirstVisiblePosition());
            if (row == null) { list.requestFocus(); return; }
            View target = named(row, label);
            (target == null ? row : target).requestFocus();
        }
        private static View named(View view, CharSequence label) {
            if (label != null && label.equals(view.getContentDescription())) return view;
            if (view instanceof ViewGroup) {
                ViewGroup group = (ViewGroup)view;
                for (int i = 0; i < group.getChildCount(); i++) {
                    View found = named(group.getChildAt(i), label);
                    if (found != null) return found;
                }
            }
            return null;
        }
    }
}
