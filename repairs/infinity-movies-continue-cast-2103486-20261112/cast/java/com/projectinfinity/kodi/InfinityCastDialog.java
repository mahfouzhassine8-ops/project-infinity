package com.projectinfinity.kodi;

import android.app.Dialog;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import org.json.JSONObject;
import java.lang.ref.WeakReference;
import java.util.Locale;

/** Explicit dialog on the current Infinity activity; no Activity or startup hook. */
public final class InfinityCastDialog extends Dialog implements InfinityCastSession.View {
    private static WeakReference<InfinityCastDialog> shown=new WeakReference<>(null);
    private final Main activity;
    private final InfinityCastSession cast;
    private final LinearLayout body,devices;
    private final TextView heading,title,status,time;
    private final Button toggle,back,close;
    private final SeekBar progress;
    private boolean light,dragging;
    private String deviceSignature="";
    private final int cyan=Color.rgb(0,193,224);

    public static void open() {
        new Handler(Looper.getMainLooper()).post(()->{
            Main activity=Main.MainActivity;
            if(activity==null || activity.isFinishing() || activity.isDestroyed())return;
            InfinityCastDialog previous=shown.get();
            if(previous!=null && previous.isShowing())return;
            try {
                InfinityCastDialog dialog=new InfinityCastDialog(activity);
                shown=new WeakReference<>(dialog);dialog.show();dialog.resize();
                dialog.cast.attach(dialog);
            } catch(RuntimeException | LinkageError unavailable) {
                // Opening a Cast control never changes the phone player.
                android.widget.Toast.makeText(activity,"Cast is unavailable. Phone playback is unchanged.",
                    android.widget.Toast.LENGTH_LONG).show();
            }
        });
    }
    private InfinityCastDialog(Main activity) {
        super(activity);this.activity=activity;requestWindowFeature(Window.FEATURE_NO_TITLE);
        light=(activity.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
            ==Configuration.UI_MODE_NIGHT_NO;
        cast=InfinityCastSession.get(activity);
        body=new LinearLayout(activity){
            @Override protected void onConfigurationChanged(Configuration next){super.onConfigurationChanged(next);resize();}
        };body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(20),dp(16),dp(20),dp(12));
        heading=text("Cast to Device",22,true);title=text("",16,true);status=text("",14,false);time=text("",14,false);
        body.addView(heading);body.addView(title);body.addView(status);
        ScrollView scroll=new ScrollView(activity);devices=new LinearLayout(activity);devices.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(devices);body.addView(scroll,new LinearLayout.LayoutParams(-1,dp(170)));
        progress=new SeekBar(activity);progress.setMax(10000);body.addView(progress,new LinearLayout.LayoutParams(-1,dp(48)));
        body.addView(time);
        toggle=button("Play / Pause",v->cast.toggle());back=button("Return to Phone / Disconnect",v->cast.returnToPhone());
        close=button("Close Controls",v->dismiss());body.addView(toggle);body.addView(back);body.addView(close);
        progress.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onStartTrackingTouch(SeekBar seek){dragging=true;}
            public void onProgressChanged(SeekBar seek,int value,boolean user){}
            public void onStopTrackingTouch(SeekBar seek){dragging=false;if(cast.duration()>0)
                cast.seek(Math.round(cast.duration()*(seek.getProgress()/10000.0)));}
        });
        ScrollView content=new ScrollView(activity);content.addView(body);setContentView(content);
        setOnDismissListener(d->{cast.detach(this);if(shown.get()==this)shown.clear();});
        applyColors();
        try {
            final WeakReference<InfinityCastDialog> weak=new WeakReference<>(this);
            InfinityCastRpc.send("XBMC.GetInfoLabels",new JSONObject().put("labels",
                new org.json.JSONArray().put("Window(Home).Property(Infinity.Theme)")),reply->{
                    InfinityCastDialog dialog=weak.get();if(dialog==null || reply==null)return;
                    String theme=reply.optJSONObject("result")==null?"":
                        reply.optJSONObject("result").optString("Window(Home).Property(Infinity.Theme)");
                    if("light".equals(theme) || "dark".equals(theme)){dialog.light="light".equals(theme);dialog.applyColors();}
                });
        } catch(Exception ignored) {}
    }
    private int dp(int value){return Math.round(value*activity.getResources().getDisplayMetrics().density);}
    private TextView text(String value,int size,boolean bold) {
        TextView view=new TextView(activity);view.setText(value);view.setTextSize(size);view.setPadding(0,dp(5),0,dp(5));
        if(bold)view.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return view;
    }
    private Button button(String value,View.OnClickListener listener) {
        Button button=new Button(activity);button.setText(value);button.setAllCaps(false);button.setMinHeight(dp(48));
        button.setOnClickListener(listener);button.setContentDescription(value);return button;
    }
    private void resize() {
        Window window=getWindow();if(window==null)return;
        int width=activity.getResources().getDisplayMetrics().widthPixels;
        int height=activity.getResources().getDisplayMetrics().heightPixels;
        window.setLayout(Math.min(width-dp(24),dp(520)),Math.min(height-dp(32),dp(640)));
        window.setGravity(Gravity.CENTER);window.setBackgroundDrawableResource(android.R.color.transparent);
    }
    private void applyColors() {
        int foreground=light?Color.rgb(15,25,31):Color.rgb(235,243,248);
        GradientDrawable background=new GradientDrawable();background.setColor(light?Color.rgb(245,249,252):Color.rgb(10,17,23));
        background.setCornerRadius(dp(20));background.setStroke(dp(1),cyan);body.setBackground(background);
        for(TextView view:new TextView[]{heading,title,status,time})view.setTextColor(foreground);
        heading.setTextColor(cyan);toggle.setTextColor(foreground);back.setTextColor(foreground);close.setTextColor(foreground);
        progress.setProgressTintList(ColorStateList.valueOf(cyan));progress.setThumbTintList(ColorStateList.valueOf(cyan));
        deviceSignature="";changed();
    }
    private static String clock(long ms) {
        long seconds=Math.max(0,ms/1000);return String.format(Locale.ROOT,"%d:%02d:%02d",seconds/3600,(seconds/60)%60,seconds%60);
    }
    @Override public void changed() {
        title.setText(cast.title());status.setText(cast.message);
        toggle.setText(cast.playing()?"Pause":"Play");toggle.setEnabled(cast.casting());
        back.setEnabled(cast.connected() || cast.hasRetainedPhone());
        progress.setEnabled(cast.casting() && cast.seekable() && cast.duration()>0);
        if(!dragging && cast.duration()>0)progress.setProgress((int)Math.min(10000,cast.position()*10000.0/cast.duration()));
        time.setText(cast.duration()>0?clock(cast.position())+" / "+clock(cast.duration()):"");
        StringBuilder signature=new StringBuilder();
        for(androidx.mediarouter.media.MediaRouter.RouteInfo route:cast.devices)signature.append(route.getId()).append('\n').append(route.getName()).append('\n');
        if(!signature.toString().equals(deviceSignature) || devices.getChildCount()==0) {
            deviceSignature=signature.toString();devices.removeAllViews();
            if(cast.devices.isEmpty()){TextView empty=text("No compatible devices found on this network.",14,false);
                empty.setTextColor(light?Color.DKGRAY:Color.LTGRAY);devices.addView(empty);}
            for(int i=0;i<cast.devices.size();i++) {
                final int index=i;Button device=button(cast.devices.get(i).getName(),v->cast.choose(index));
                device.setTextColor(light?Color.BLACK:Color.WHITE);devices.addView(device);
            }
        }
    }
}
