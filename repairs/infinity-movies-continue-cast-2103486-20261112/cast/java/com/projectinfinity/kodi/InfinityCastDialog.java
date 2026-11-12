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

/** Compact Cast-only controls on the existing Infinity Activity. */
public final class InfinityCastDialog extends Dialog implements InfinityCastSession.View {
    private static WeakReference<InfinityCastDialog> shown=new WeakReference<>(null);
    private final Main activity;
    private final InfinityCastSession cast;
    private final LinearLayout body,devices,transport;
    private final ScrollView receiverScroll;
    private final TextView heading,title,status,time,receiver;
    private final Button toggle,back,close;
    private final SeekBar progress;
    private boolean light,dragging;
    private String deviceSignature="";
    private final int cyan=Color.rgb(0,193,224);
    public static void open() {
        new Handler(Looper.getMainLooper()).post(()->{
            Main activity=Main.MainActivity;
            if(activity==null || activity.isFinishing() || activity.isDestroyed())return;
            InfinityCastDialog previous=shown.get();if(previous!=null && previous.isShowing())return;
            try {
                InfinityCastDialog dialog=new InfinityCastDialog(activity);shown=new WeakReference<>(dialog);
                dialog.show();dialog.resize();dialog.cast.attach(dialog);
            } catch(RuntimeException | LinkageError unavailable) {
                android.widget.Toast.makeText(activity,"Cast is unavailable. Phone playback is unchanged.",android.widget.Toast.LENGTH_LONG).show();
            }
        });
    }
    private InfinityCastDialog(Main activity) {
        super(activity);this.activity=activity;requestWindowFeature(Window.FEATURE_NO_TITLE);
        light=(activity.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_NO;
        cast=InfinityCastSession.get(activity);
        body=new LinearLayout(activity){@Override protected void onConfigurationChanged(Configuration next){super.onConfigurationChanged(next);resize();}};
        body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(18),dp(14),dp(18),dp(12));
        heading=text("Cast to Device",20,true);title=text("",16,true);receiver=text("",14,false);status=text("",14,false);
        body.addView(heading);body.addView(title);body.addView(receiver);body.addView(status);
        receiverScroll=new ScrollView(activity);devices=new LinearLayout(activity);devices.setOrientation(LinearLayout.VERTICAL);receiverScroll.addView(devices);
        body.addView(receiverScroll,new LinearLayout.LayoutParams(-1,-2));
        transport=new LinearLayout(activity);transport.setOrientation(LinearLayout.VERTICAL);
        time=text("",13,false);transport.addView(time);progress=new SeekBar(activity);progress.setMax(10000);
        progress.setContentDescription("Playback position");transport.addView(progress,new LinearLayout.LayoutParams(-1,dp(40)));
        toggle=button("Pause",v->cast.toggle());transport.addView(toggle);body.addView(transport);
        back=button("Return to Phone / Disconnect",v->cast.returnToPhone());close=button("Close Controls",v->dismiss());body.addView(back);body.addView(close);
        progress.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onStartTrackingTouch(SeekBar seek){dragging=true;}
            public void onProgressChanged(SeekBar seek,int value,boolean user){if(user && cast.duration()>0)time.setText("Playback position  "+clock(Math.round(cast.duration()*value/10000.0))+" / "+clock(cast.duration()));}
            public void onStopTrackingTouch(SeekBar seek){dragging=false;if(cast.duration()>0)cast.seek(Math.round(cast.duration()*seek.getProgress()/10000.0));}
        });
        ScrollView content=new ScrollView(activity){@Override protected void onMeasure(int width,int height){
            int limit=Math.max(dp(160),activity.getResources().getDisplayMetrics().heightPixels-dp(64));
            super.onMeasure(width,View.MeasureSpec.makeMeasureSpec(limit,View.MeasureSpec.AT_MOST));
        }};
        content.setFillViewport(false);content.addView(body);setContentView(content);
        setOnDismissListener(d->{cast.detach(this);if(shown.get()==this)shown.clear();});applyColors();
        try {
            WeakReference<InfinityCastDialog> weak=new WeakReference<>(this);
            InfinityCastRpc.send("XBMC.GetInfoLabels",new JSONObject().put("labels",new org.json.JSONArray().put("Window(Home).Property(Infinity.Theme)")),reply->{
                InfinityCastDialog dialog=weak.get();if(dialog==null || reply==null)return;
                String theme=reply.optJSONObject("result")==null?"":reply.optJSONObject("result").optString("Window(Home).Property(Infinity.Theme)");
                if("light".equals(theme) || "dark".equals(theme)){dialog.light="light".equals(theme);dialog.applyColors();}
            });
        } catch(Exception ignored){}
    }
    private int dp(int value){return Math.round(value*activity.getResources().getDisplayMetrics().density);}
    private TextView text(String value,int size,boolean bold) {
        TextView view=new TextView(activity);view.setText(value);view.setTextSize(size);view.setPadding(0,dp(4),0,dp(4));if(bold)view.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return view;
    }
    private Button button(String value,View.OnClickListener listener) {
        Button button=new Button(activity);button.setText(value);button.setAllCaps(false);button.setMinHeight(dp(44));button.setTextSize(14);
        button.setOnClickListener(listener);button.setContentDescription(value);return button;
    }
    private void resize() {
        Window window=getWindow();if(window==null)return;
        int width=activity.getResources().getDisplayMetrics().widthPixels;
        window.setLayout(Math.min(width-dp(24),dp(420)),WindowManager.LayoutParams.WRAP_CONTENT);
        window.setGravity(Gravity.CENTER);window.setBackgroundDrawableResource(android.R.color.transparent);
    }
    private void applyColors() {
        int foreground=light?Color.rgb(15,25,31):Color.rgb(235,243,248);
        GradientDrawable background=new GradientDrawable();background.setColor(light?Color.rgb(245,249,252):Color.rgb(10,17,23));background.setCornerRadius(dp(16));background.setStroke(dp(1),cyan);body.setBackground(background);
        for(TextView view:new TextView[]{heading,title,status,time,receiver})view.setTextColor(foreground);heading.setTextColor(cyan);receiver.setTextColor(cyan);
        for(Button button:new Button[]{toggle,back,close}){button.setTextColor(foreground);button.setBackgroundTintList(ColorStateList.valueOf(light?Color.rgb(225,235,241):Color.rgb(26,40,50)));}
        progress.setProgressTintList(ColorStateList.valueOf(cyan));progress.setThumbTintList(ColorStateList.valueOf(cyan));deviceSignature="";changed();
    }
    private static String clock(long ms){long s=Math.max(0,ms/1000);return s>=3600?String.format(Locale.ROOT,"%d:%02d:%02d",s/3600,(s/60)%60,s%60):String.format(Locale.ROOT,"%d:%02d",s/60,s%60);}
    @Override public void changed() {
        title.setText(InfinityCastSource.receiverTitle(cast.title()));status.setText(cast.message);
        boolean active=cast.casting(),busy=cast.transferring();
        transport.setVisibility(active?View.VISIBLE:View.GONE);receiverScroll.setVisibility(active || busy?View.GONE:View.VISIBLE);
        receiver.setText(cast.receiverName().isEmpty()?"":"TV · "+cast.receiverName());receiver.setVisibility((active || busy) && !cast.receiverName().isEmpty()?View.VISIBLE:View.GONE);
        back.setVisibility(cast.canDisconnect()?View.VISIBLE:View.GONE);back.setText(active?"Return to Phone / Disconnect":"Cancel Cast / Disconnect");
        toggle.setText(cast.playing()?"Pause":"Resume");toggle.setEnabled(active);
        progress.setEnabled(active && cast.seekable() && cast.duration()>0);
        if(!dragging){if(cast.duration()>0)progress.setProgress((int)Math.min(10000,cast.position()*10000.0/cast.duration()));time.setText(cast.duration()>0?"Playback position  "+clock(cast.position())+" / "+clock(cast.duration()):"Playback position unavailable");}
        StringBuilder signature=new StringBuilder();for(androidx.mediarouter.media.MediaRouter.RouteInfo route:cast.devices)signature.append(route.getId()).append('\n').append(route.getName()).append('\n');
        if(!signature.toString().equals(deviceSignature) || devices.getChildCount()==0) {
            deviceSignature=signature.toString();devices.removeAllViews();
            if(cast.devices.isEmpty()){TextView empty=text("No compatible video receivers found on this network.",14,false);empty.setTextColor(light?Color.DKGRAY:Color.LTGRAY);devices.addView(empty);}
            for(int i=0;i<cast.devices.size();i++){final int index=i;Button device=button(cast.devices.get(i).getName(),v->cast.choose(index));device.setTextColor(light?Color.BLACK:Color.WHITE);devices.addView(device);}
        }
    }
}
