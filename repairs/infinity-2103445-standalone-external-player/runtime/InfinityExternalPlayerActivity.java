package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.SeekBar;
import android.widget.TextView;
import java.util.Locale;

/** Private external-video UI. Resume history has no Kodi/Cobra/service dependencies. */
public final class InfinityExternalPlayerActivity extends Activity implements InfinityExternalEngine.Observer {
    private final InfinityExternalState state = new InfinityExternalState();
    private InfinityExternalEngine engine;
    private long token;
    private FrameLayout root, picture;
    private SurfaceView video;
    private LinearLayout controls, top, notice, toolbar, timeline, controlRow;
    private TextView totalTime;
    private SeekBar inlineVolume;
    private InfinityPreviewChrome chrome;
    private InfinityPreviewChrome.Brand brand;
    private int appearance;
    private TextView title, message, times, subtitles;
    private ProgressBar busy;
    private Button play, mute, rotation, retry;
    private SeekBar seek;
    private boolean started, ready, wantsPlay = true, muted, dragging, filling, locked;
    private boolean focusHeld, focusResume;
    private int position, duration, width, height;
    private float level = 1f;
    private AudioManager audio;
    private AudioFocusRequest focusRequest;
    private AudioManager.OnModeChangedListener callModeListener;
    private boolean callActive, callMuted;
    private String requestId;
    private boolean offerResume = true;
    private long resumePosition;
    private AlertDialog resumeDialog;
    private final AudioManager.OnAudioFocusChangeListener focus = change -> runOnUiThread(() -> {
        if (engine == null || isFinishing()) return;
        syncCallMode(false);
        if (change == AudioManager.AUDIOFOCUS_GAIN) {
            focusHeld = true;
            if (focusResume && started) { focusResume = false; wantsPlay = true; startPlayback(); }
        } else if (change == AudioManager.AUDIOFOCUS_LOSS || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT
                || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK) {
            if (callActive) { focusHeld=false; focusResume=false; return; }
            focusResume = change != AudioManager.AUDIOFOCUS_LOSS && wantsPlay;
            focusHeld = false; wantsPlay = false; engine.pause();
        }
    });
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        audio = (AudioManager)getSystemService(AUDIO_SERVICE);
        engine = new InfinityExternalEngine(this, this);
        muted = existingExperiencePresent();
        if (saved != null) {
            position = saved.getInt("position"); muted = saved.getBoolean("muted");
            wantsPlay = saved.getBoolean("play"); level = saved.getFloat("level", 1f);
            filling = saved.getBoolean("fill"); locked = saved.getBoolean("locked");
        }
        boolean restored = saved != null && saved.getString("preview.request") != null
                && saved.getString("preview.request").equals(getIntent().getStringExtra("infinity.external.request"));
        if (restored) offerResume = saved.getBoolean("preview.offerResume", true);
        callActive=isCallMode(audio.getMode());
        callMuted=callActive && !(saved!=null && saved.getBoolean("preview.callActive") && !saved.getBoolean("preview.callMuted",true));
        if(Build.VERSION.SDK_INT>=31){
            callModeListener=mode->{if(!isFinishing()&&engine!=null)syncCallMode(hasWindowFocus());};
            audio.addOnModeChangedListener(getMainExecutor(),callModeListener);
        }
        buildUi(); accept(getIntent(), restored);
    }
    private boolean existingExperiencePresent() {
        ActivityManager manager = (ActivityManager)getSystemService(ACTIVITY_SERVICE);
        // Do not take audio focus automatically from an existing experience.
        // A deliberate Unmute is the user's choice to move audio focus.
        for (ActivityManager.AppTask task : manager.getAppTasks()) {
            ActivityManager.RecentTaskInfo info = task.getTaskInfo();
            android.content.ComponentName base = Build.VERSION.SDK_INT >= 23 ? info.baseActivity : info.baseIntent.getComponent();
            if (base != null && (base.getClassName().equals("com.projectinfinity.kodi.Main")
                    || base.getClassName().equals("com.projectinfinity.kodi.InfinityLiveActivity"))) return true;
        }
        return false;
    }
    private void accept(Intent request, boolean restored) {
        String id = request == null ? null : request.getStringExtra("infinity.external.request");
        if (id == null) id = java.util.UUID.randomUUID().toString();
        long next = state.begin(id); if (next < 0) return;
        dismissResume(); resumePosition = 0;
        token = next; requestId = id; ready = false;
        setIntent(request);
        if (!restored) { position = 0; wantsPlay = true; offerResume = true; }
        duration = 0; width = height = 0; subtitles.setText(""); seek.setProgress(0); seek.setEnabled(false);
        String name = request != null && request.getData() != null ? request.getData().getLastPathSegment() : null;
        title.setText(name == null || name.isEmpty() ? "Infinity video" : name);
        if (started) load();
    }
    @Override protected void onNewIntent(Intent intent) { super.onNewIntent(intent); accept(intent, false); }
    private void load() {
        ready = false; state.set(token, InfinityExternalState.Phase.OPENING); showStatus("Loading…", true);
        resumePosition = 0;
        engine.volume(effectiveMuted() ? 0f : level); engine.open(getIntent(), position, offerResume); updateButtons();
    }
    @Override protected void onStart() { super.onStart(); started = true; syncCallMode(false); load(); }
    @Override protected void onPause() {
        engine.pause(); abandonFocus(); super.onPause();
    }
    @Override protected void onStop() {
        dismissResume();
        started = false; ready = false; engine.suspend(); abandonFocus();
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); super.onStop();
    }
    @Override protected void onDestroy() {
        if(Build.VERSION.SDK_INT>=31 && callModeListener!=null)audio.removeOnModeChangedListener(callModeListener);
        state.release(); engine.destroy(); abandonFocus(); super.onDestroy();
    }
    @Override protected void onSaveInstanceState(Bundle out) {
        out.putInt("position", position); out.putBoolean("muted", muted); out.putBoolean("play", wantsPlay);
        out.putFloat("level", level); out.putBoolean("fill", filling); out.putBoolean("locked", locked);
        out.putBoolean("preview.callActive",callActive);out.putBoolean("preview.callMuted",callMuted);
        out.putString("preview.request", requestId); out.putBoolean("preview.offerResume", offerResume);
        super.onSaveInstanceState(out);
    }
    @Override public void onConfigurationChanged(Configuration config) { super.onConfigurationChanged(config); applyChrome(); layoutChrome(); fitVideo(); }
    @Override public void onBackPressed() { close(); }
    private void close() {
        dismissResume();
        wantsPlay = false; state.release(); engine.suspend(); abandonFocus(); finish();
    }
    private static boolean isCallMode(int mode) {
        // AudioManager mode is observable without phone-state/contact permissions.
        return mode==AudioManager.MODE_IN_CALL || mode==AudioManager.MODE_IN_COMMUNICATION
                || (Build.VERSION.SDK_INT>=33 && (mode==AudioManager.MODE_CALL_REDIRECT || mode==AudioManager.MODE_COMMUNICATION_REDIRECT));
    }
    private boolean effectiveMuted() { return muted || callMuted; }
    private void syncCallMode(boolean continuePlayback) {
        boolean active=isCallMode(audio.getMode());if(active==callActive)return;
        boolean interrupted=focusResume && started;callActive=active;
        if(active){
            callMuted=true;abandonFocus();if(interrupted)wantsPlay=true;
        }else callMuted=false;
        // Restore ordinary focus ownership before restoring sound after a call.
        boolean maySound=effectiveMuted() || !started || !ready || !wantsPlay || active || obtainFocus();
        engine.volume(effectiveMuted()||!maySound?0f:level);
        if(!maySound){wantsPlay=false;engine.pause();showStatus("Audio is in use. Press Play to retry.",false);}
        updateButtons();
        if(continuePlayback && started && ready && wantsPlay)startPlayback();
    }
    private boolean obtainFocus() {
        if (effectiveMuted() || focusHeld) return true;
        int result;
        if (Build.VERSION.SDK_INT >= 26) {
            focusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
                    .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MOVIE).build())
                    .setOnAudioFocusChangeListener(focus).build();
            result = audio.requestAudioFocus(focusRequest);
        } else result = audio.requestAudioFocus(focus, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT);
        focusHeld = result == AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
        // Only a deliberate Unmute can remove the per-call automatic mute.
        // Media remains USAGE_MEDIA; Android/carrier muting still applies.
        return focusHeld || callActive;
    }
    private void abandonFocus() {
        focusResume = false;
        if (focusRequest != null && Build.VERSION.SDK_INT >= 26) audio.abandonAudioFocusRequest(focusRequest);
        else if (audio != null && focusHeld) audio.abandonAudioFocus(focus);
        focusRequest = null; focusHeld = false;
    }
    private void startPlayback() {
        if (!ready || !started || !wantsPlay || resumePosition > 0) return;
        syncCallMode(false);
        if (!wantsPlay) return;
        if (!obtainFocus()) { wantsPlay = false; showStatus("Audio is in use. Press Play to retry.", false); updateButtons(); return; }
        engine.play();
    }
    private void dismissResume() {
        if (resumeDialog != null) { resumeDialog.dismiss(); resumeDialog = null; }
    }
    private void showResume() {
        dismissResume(); final long choiceToken = token;
        resumeDialog = dialog().setTitle("Resume video?")
                .setMessage("Continue from " + time((int)resumePosition) + "?")
                .setPositiveButton("Resume", (dialog, which) -> chooseResume(choiceToken, true))
                .setNegativeButton("Start Over", (dialog, which) -> chooseResume(choiceToken, false))
                .setOnCancelListener(dialog -> { if (choiceToken == token) close(); }).create();
        resumeDialog.setCanceledOnTouchOutside(false); resumeDialog.show();
    }
    private void chooseResume(long choiceToken, boolean restore) {
        if (choiceToken != token || !started || !ready) return;
        resumeDialog = null; offerResume = false;
        showStatus("Seeking…", true); engine.chooseResume(restore);
    }
    @Override public void event(String event, String detail) {
        if (!started || isFinishing()) return;
        android.util.Log.i("InfinityExternalPlayer", event); // No private URI, title, headers or source extras.
        switch (event) {
            case "opening": state.set(token, InfinityExternalState.Phase.OPENING); showStatus("Loading…", true); break;
            case "preparing": state.set(token, InfinityExternalState.Phase.PREPARING); showStatus("Loading…", true); break;
            case "ready":
                ready = true; state.set(token, InfinityExternalState.Phase.READY); showStatus("", false);
                if (resumePosition > 0) showResume();
                else { offerResume = false; if (wantsPlay) startPlayback(); else event("paused", ""); } break;
            case "resume": resumePosition = Long.parseLong(detail); break;
            case "resume_ready": case "resume_unavailable":
                dismissResume(); resumePosition = 0; offerResume = false;
                showStatus("", false);
                if (ready && wantsPlay) startPlayback(); break;
            case "history_unavailable":
                android.widget.Toast.makeText(this, detail, android.widget.Toast.LENGTH_LONG).show(); break;
            case "frame": case "playing":
                state.set(token, InfinityExternalState.Phase.PLAYING); showStatus("", false);
                getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); break;
            case "buffering": showStatus("Buffering…", true); break;
            case "paused":
                state.set(token, InfinityExternalState.Phase.PAUSED); showStatus("", false);
                getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); break;
            case "ended":
                wantsPlay = false; state.set(token, InfinityExternalState.Phase.ENDED); showStatus("Video ended", false);
                abandonFocus(); getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); break;
            case "error":
                dismissResume(); resumePosition = 0;
                ready = false; wantsPlay = false; state.set(token, InfinityExternalState.Phase.ERROR);
                showStatus(detail, false); abandonFocus();
                getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); break;
            case "not_seekable": seek.setEnabled(false); break;
        }
        updateButtons();
    }
    @Override public void position(int now, int total) {
        position = now; duration = total;
        showTimes(now, total);
        seek.setEnabled(ready && total > 0);
        if (!dragging) { seek.setMax(Math.max(total, 1)); seek.setProgress(Math.max(0, now)); }
    }
    @Override public void size(int w, int h) { width = w; height = h; fitVideo(); }
    @Override public void subtitle(String text) { subtitles.setText(text); }
    @Override public void tracks(String[] labels, int[] indexes, int selected, boolean caption) {
        if (isFinishing() || !started) return;
        if (labels.length == 0 || (caption && labels.length == 1)) {
            dialog().setTitle(caption ? "Subtitles" : "Audio")
                    .setMessage(caption ? "No supported text subtitle tracks in this video." : "No selectable audio tracks in this video.")
                    .setPositiveButton("OK", null).show(); return;
        }
        int checked = -1;
        for (int i = 0; i < indexes.length; i++) if (indexes[i] == selected) checked = i;
        dialog().setTitle(caption ? "Subtitles" : "Audio")
                .setSingleChoiceItems(labels, checked, (dialog, which) -> {
                    engine.selectTrack(indexes[which], caption); if (caption) subtitles.setText(""); dialog.dismiss();
                }).setNegativeButton("Cancel", null).show();
    }
    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }
    private AlertDialog.Builder dialog() {
        return new AlertDialog.Builder(new android.view.ContextThemeWrapper(this,
                chrome != null && chrome.light ? android.R.style.Theme_Material_Light_Dialog_Alert : android.R.style.Theme_Material_Dialog_Alert));
    }
    private TextView text(int sp) {
        TextView t = new TextView(this); t.setTextColor(chrome.ink); t.setTextSize(sp); t.setTypeface(chrome.font); return t;
    }
    private Button button(String label, Runnable click) {
        Button b = new InfinityPreviewChrome.Control(this, chrome); b.setAllCaps(false); b.setText(label); b.setContentDescription(label);
        b.setOnClickListener(v -> click.run()); return b;
    }
    private void addControl(View child, int widthDp) {
        float fontScale = Math.max(1f, getResources().getConfiguration().fontScale);
        child.setTag(new int[]{widthDp,52});
        controlRow.addView(child,new LinearLayout.LayoutParams(dp(Math.round(widthDp*fontScale)),dp(52)));
    }
    private void separator(int before, int after) {
        View line = new View(this); line.setTag(new int[]{1,24,before,after}); line.setBackgroundColor(chrome.track);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(dp(1),dp(24));p.setMargins(dp(before),0,dp(after),0);controlRow.addView(line,p);
    }
    private void buildUi() {
        appearance=getSharedPreferences("infinity_preview_ui",MODE_PRIVATE).getInt("appearance",0);
        chrome=new InfinityPreviewChrome(this,isLight());
        root = new FrameLayout(this); root.setBackground(chrome.backdrop()); setContentView(root);
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom()); layoutChrome(); return insets;
        });
        picture = new FrameLayout(this); root.addView(picture, new FrameLayout.LayoutParams(-1,-1));
        GradientDrawable black = new GradientDrawable();black.setColor(Color.BLACK);black.setCornerRadius(dp(10));
        picture.setBackground(black);picture.setClipToOutline(true);picture.setForeground(chrome.glass(10,true));
        video = new SurfaceView(this); picture.addView(video,new FrameLayout.LayoutParams(-1,-1,Gravity.CENTER));
        video.getHolder().addCallback(new SurfaceHolder.Callback() {
            public void surfaceCreated(SurfaceHolder h) { engine.surface(h.getSurface()); }
            public void surfaceChanged(SurfaceHolder h,int format,int w,int he) { engine.surface(h.getSurface()); }
            public void surfaceDestroyed(SurfaceHolder h) { engine.surface(null); }
        });
        picture.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob) -> {if(r-l!=or-ol||b-t!=ob-ot)fitVideo();});
        video.setOnClickListener(v -> {
            boolean visible=controls.getVisibility()==View.VISIBLE;
            controls.setVisibility(visible?View.GONE:View.VISIBLE);top.setVisibility(visible?View.GONE:View.VISIBLE);
        });
        subtitles=text(20);subtitles.setTextColor(Color.WHITE);subtitles.setGravity(Gravity.CENTER);subtitles.setShadowLayer(3,1,1,Color.BLACK);
        FrameLayout.LayoutParams sub=new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM);sub.bottomMargin=dp(12);picture.addView(subtitles,sub);
        top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);top.setPadding(dp(10),0,dp(8),0);
        top.setBackground(new android.graphics.drawable.InsetDrawable(chrome.glass(14,false),0,dp(4),0,dp(4)));
        top.addView(button("Close",this::close),new LinearLayout.LayoutParams(dp(68),dp(48)));
        View headerDivider=new View(this);headerDivider.setTag("preview.divider");headerDivider.setBackgroundColor(chrome.secondary);
        LinearLayout.LayoutParams divide=new LinearLayout.LayoutParams(dp(1),dp(14));divide.setMargins(dp(13),0,dp(15),0);top.addView(headerDivider,divide);
        title=text(12);title.setMaxLines(1);title.setGravity(Gravity.CENTER_VERTICAL);title.setEllipsize(android.text.TextUtils.TruncateAt.MIDDLE);
        top.addView(title,new LinearLayout.LayoutParams(0,-1,1));brand=new InfinityPreviewChrome.Brand(this,chrome);
        top.addView(brand,new LinearLayout.LayoutParams(dp(108),-1));root.addView(top,new FrameLayout.LayoutParams(-1,dp(48),Gravity.TOP));
        notice=new LinearLayout(this);notice.setOrientation(LinearLayout.VERTICAL);notice.setGravity(Gravity.CENTER);notice.setPadding(dp(20),dp(12),dp(20),dp(12));
        busy=new ProgressBar(this);busy.setIndeterminateTintList(android.content.res.ColorStateList.valueOf(chrome.accent));notice.addView(busy,new LinearLayout.LayoutParams(dp(32),dp(32)));
        message=text(16);message.setGravity(Gravity.CENTER);notice.addView(message);retry=button("Retry",()->{wantsPlay=true;load();});
        notice.addView(retry,new LinearLayout.LayoutParams(dp(88),dp(48)));root.addView(notice,new FrameLayout.LayoutParams(-1,-2,Gravity.CENTER));
        controls=new LinearLayout(this);controls.setOrientation(LinearLayout.VERTICAL);
        timeline=new LinearLayout(this);timeline.setGravity(Gravity.CENTER_VERTICAL);timeline.setPadding(dp(11),0,dp(12),0);
        times=text(10);times.setContentDescription("Elapsed time");timeline.addView(times,new LinearLayout.LayoutParams(dp(32),-2));
        seek=new SeekBar(this);seek.setContentDescription("Seek video");seek.setPadding(dp(8),0,dp(8),0);chrome.seek(seek);timeline.addView(seek,new LinearLayout.LayoutParams(0,dp(42),1));
        totalTime=text(10);totalTime.setGravity(Gravity.RIGHT);totalTime.setContentDescription("Total time");timeline.addView(totalTime,new LinearLayout.LayoutParams(dp(27),-2));
        controls.addView(timeline,new LinearLayout.LayoutParams(-1,dp(42)));
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onStartTrackingTouch(SeekBar s) {dragging=true;}
            public void onProgressChanged(SeekBar s,int value,boolean user) {if(user)showTimes(value,duration);}
            public void onStopTrackingTouch(SeekBar s) {dragging=false;engine.seek(s.getProgress());}
        });
        toolbar=new LinearLayout(this);toolbar.setGravity(Gravity.CENTER_VERTICAL);toolbar.setPadding(dp(12),0,dp(4),0);toolbar.setBackground(chrome.glass(16,false));
        HorizontalScrollView strip=new HorizontalScrollView(this);strip.setHorizontalScrollBarEnabled(false);strip.setFillViewport(false);
        controlRow=new LinearLayout(this);controlRow.setGravity(Gravity.CENTER_VERTICAL);strip.addView(controlRow);
        play=button("Pause",()->{
            wantsPlay=!wantsPlay;
            if(wantsPlay){
                if(state.phase()==InfinityExternalState.Phase.ENDED||(duration>0&&position>=duration-250)){position=0;engine.seek(0);}
                startPlayback();
            }else{engine.pause();abandonFocus();}
            updateButtons();
        });addControl(play,52);addControl(button("Stop",this::close),48);separator(0,5);
        addControl(button("−10 s",()->engine.seek(Math.max(0,position-10000))),52);
        addControl(button("+10 s",()->engine.seek(duration>0?Math.min(duration,position+10000):position+10000)),52);separator(9,0);
        mute=button("Mute",()->{
            if(callMuted){callMuted=false;muted=false;}else muted=!muted;engine.volume(effectiveMuted()?0:level);
            if(muted)abandonFocus();else if(!obtainFocus()){muted=true;engine.volume(0);}
            updateButtons();
        });addControl(mute,48);
        inlineVolume=new SeekBar(this);inlineVolume.setMax(100);inlineVolume.setProgress(Math.round(level*100));inlineVolume.setContentDescription("Player volume");chrome.seek(inlineVolume);
        inlineVolume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){}
            public void onProgressChanged(SeekBar s,int value,boolean user){if(user){level=value/100f;engine.volume(effectiveMuted()?0:level);}}
        });addControl(inlineVolume,104);separator(14,12);
        addControl(button("Audio",()->engine.listTracks(false)),52);addControl(button("Subtitles",()->engine.listTracks(true)),64);
        addControl(button("Display",()->dialog().setTitle("Display")
                .setSingleChoiceItems(new String[]{"Best Fit","Fill (crop)"},filling?1:0,(d,which)->{filling=which==1;fitVideo();d.dismiss();})
                .setNeutralButton("Appearance",(d,which)->showAppearance()).setNegativeButton("Cancel",null).show()),56);
        rotation=button("Auto rotate",()->{
            locked=!locked;setRequestedOrientation(locked?android.content.pm.ActivityInfo.SCREEN_ORIENTATION_LOCKED:android.content.pm.ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR);updateButtons();
        });addControl(rotation,72);
        // Keep the original Volume dialog available after the primary mockup controls.
        addControl(button("Volume",()->{
            SeekBar volume=new SeekBar(this);volume.setMax(100);volume.setProgress(Math.round(level*100));volume.setContentDescription("Player volume");chrome.seek(volume);
            volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
                public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){}
                public void onProgressChanged(SeekBar s,int value,boolean user){if(user){level=value/100f;inlineVolume.setProgress(value);engine.volume(effectiveMuted()?0:level);}}
            });dialog().setTitle("Player volume").setView(volume).setPositiveButton("Done",null).show();
        }),52);
        toolbar.addView(strip,new LinearLayout.LayoutParams(-1,-1));LinearLayout.LayoutParams bar=new LinearLayout.LayoutParams(-1,dp(70));bar.topMargin=dp(6);controls.addView(toolbar,bar);
        root.addView(controls,new FrameLayout.LayoutParams(-1,dp(118),Gravity.BOTTOM));
        root.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol||b-t!=ob-ot)layoutChrome();});
        root.requestApplyInsets();applyChrome();showTimes(position,duration);updateButtons();
    }
    private boolean isLight() {
        return appearance==1||(appearance==0&&(getResources().getConfiguration().uiMode&Configuration.UI_MODE_NIGHT_MASK)!=Configuration.UI_MODE_NIGHT_YES);
    }
    private void showAppearance() {
        dialog().setTitle("Preview appearance").setSingleChoiceItems(new String[]{"System","Light","Dark"},appearance,(d,which)->{
            appearance=which;getSharedPreferences("infinity_preview_ui",MODE_PRIVATE).edit().putInt("appearance",which).apply();applyChrome();d.dismiss();
        }).setNegativeButton("Cancel",null).show();
    }
    private void applyChrome() {
        if(root==null)return;chrome=new InfinityPreviewChrome(this,isLight());root.setBackground(chrome.backdrop());
        resizeChromeControls();
        top.setBackground(new android.graphics.drawable.InsetDrawable(chrome.glass(14,false),0,dp(4),0,dp(4)));toolbar.setBackground(chrome.glass(16,false));picture.setForeground(chrome.glass(10,true));
        tintTree(top);tintTree(controlRow);title.setTextColor(chrome.ink);message.setTextColor(chrome.ink);times.setTextColor(chrome.secondary);totalTime.setTextColor(chrome.secondary);
        ((InfinityPreviewChrome.Control)retry).theme(chrome);brand.theme(chrome);chrome.seek(seek);chrome.seek(inlineVolume);busy.setIndeterminateTintList(android.content.res.ColorStateList.valueOf(chrome.accent));
        int color=chrome.light?0xffedf5f7:0xff001014;getWindow().setStatusBarColor(color);getWindow().setNavigationBarColor(color);
        int mask=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;if(Build.VERSION.SDK_INT>=26)mask|=View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        int flags=getWindow().getDecorView().getSystemUiVisibility();getWindow().getDecorView().setSystemUiVisibility((flags&~mask)|(chrome.light?mask:0));
    }
    private void tintTree(View view) {
        if(view instanceof InfinityPreviewChrome.Control)((InfinityPreviewChrome.Control)view).theme(chrome);
        else if("preview.divider".equals(view.getTag())||(view.getTag() instanceof int[]&&((int[])view.getTag()).length==4))view.setBackgroundColor(chrome.track);
        if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++)tintTree(((ViewGroup)view).getChildAt(i));
    }
    private void resizeChromeControls() {
        // Android reports density changes in-place for this existing Activity.
        // Re-measure the same controls; do not replace the surface or decoder.
        float scale=Math.max(1f,getResources().getConfiguration().fontScale);
        for(int i=0;i<controlRow.getChildCount();i++){
            View child=controlRow.getChildAt(i);int[] d=(int[])child.getTag();
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(d.length==2?Math.round(d[0]*scale):d[0]),dp(d[1]));
            if(d.length==4)p.setMargins(dp(d[2]),0,dp(d[3]),0);child.setLayoutParams(p);
        }
        top.setPadding(dp(10),0,dp(8),0);top.getChildAt(0).setLayoutParams(new LinearLayout.LayoutParams(dp(68),dp(48)));
        LinearLayout.LayoutParams divider=new LinearLayout.LayoutParams(dp(1),dp(14));divider.setMargins(dp(13),0,dp(15),0);top.getChildAt(1).setLayoutParams(divider);
        toolbar.setPadding(dp(12),0,dp(4),0);timeline.setPadding(dp(11),0,dp(12),0);
        title.setTextSize(12);message.setTextSize(16);times.setTextSize(10);totalTime.setTextSize(10);subtitles.setTextSize(20);
        times.setLayoutParams(new LinearLayout.LayoutParams(dp(Math.round(32*scale)),-2));totalTime.setLayoutParams(new LinearLayout.LayoutParams(dp(Math.round(27*scale)),-2));
        seek.setPadding(dp(8),0,dp(8),0);seek.setLayoutParams(new LinearLayout.LayoutParams(0,dp(42),1));
        notice.setPadding(dp(20),dp(12),dp(20),dp(12));busy.setLayoutParams(new LinearLayout.LayoutParams(dp(32),dp(32)));retry.setLayoutParams(new LinearLayout.LayoutParams(dp(88),dp(48)));
        FrameLayout.LayoutParams sub=(FrameLayout.LayoutParams)subtitles.getLayoutParams();sub.bottomMargin=dp(12);subtitles.setLayoutParams(sub);
        GradientDrawable black=new GradientDrawable();black.setColor(Color.BLACK);black.setCornerRadius(dp(10));picture.setBackground(black);
    }
    private void place(View child,int w,int h,int left,int topMargin,int gravity,int bottom) {
        FrameLayout.LayoutParams old=(FrameLayout.LayoutParams)child.getLayoutParams();
        if(old.width==w&&old.height==h&&old.leftMargin==left&&old.topMargin==topMargin&&old.gravity==gravity&&old.bottomMargin==bottom)return;
        FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(w,h,gravity);p.leftMargin=left;p.topMargin=topMargin;p.bottomMargin=bottom;child.setLayoutParams(p);
    }
    private void layoutChrome() {
        if(root==null||controls==null)return;
        int w=root.getWidth()-root.getPaddingLeft()-root.getPaddingRight(),h=root.getHeight()-root.getPaddingTop()-root.getPaddingBottom();if(w<=0||h<=0)return;
        boolean shortWindow=h<dp(420);int bottom=dp(shortWindow?8:30),barH=dp(shortWindow?56:70),lineH=dp(shortWindow?36:42),gap=dp(shortWindow?4:6),controlsH=barH+lineH+gap;
        LinearLayout.LayoutParams a=(LinearLayout.LayoutParams)timeline.getLayoutParams();if(a.height!=lineH){a.height=lineH;timeline.setLayoutParams(a);}
        LinearLayout.LayoutParams b=(LinearLayout.LayoutParams)toolbar.getLayoutParams();if(b.height!=barH||b.topMargin!=gap){b.height=barH;b.topMargin=gap;toolbar.setLayoutParams(b);}
        place(top,w-dp(20),dp(48),dp(10),dp(5),Gravity.TOP|Gravity.LEFT,0);
        int brandW=dp(w>=dp(520)?108:28);if(brand.getLayoutParams().width!=brandW){brand.getLayoutParams().width=brandW;brand.requestLayout();}
        place(controls,w-dp(22),controlsH,dp(11),0,Gravity.BOTTOM|Gravity.LEFT,bottom);
        int upper=dp(69),lower=h-bottom-controlsH-dp(16),pw=Math.max(dp(48),w-dp(32));
        int ph=Math.max(1,Math.min(Math.round(pw*9f/16f),lower-upper));
        place(picture,pw,ph,dp(16),Math.max(dp(53),upper+(lower-upper-ph)/2),Gravity.TOP|Gravity.LEFT,0);
        fitVideo();
    }
    private void showTimes(int now,int total) {
        if(times==null)return;times.setText(time(now));totalTime.setText(total>0?time(total):"Live");
        times.setContentDescription("Elapsed time "+time(now));totalTime.setContentDescription("Total time "+(total>0?time(total):"Live"));
    }
    private void showStatus(String text, boolean loading) {
        message.setText(text); busy.setVisibility(loading ? View.VISIBLE : View.GONE);
        retry.setVisibility(state.phase() == InfinityExternalState.Phase.ERROR ? View.VISIBLE : View.GONE);
        notice.setVisibility(text.isEmpty() ? View.GONE : View.VISIBLE);
    }
    private void updateButtons() {
        if (play == null) return;
        String p = wantsPlay ? "Pause" : "Play"; play.setText(p); play.setContentDescription(p); play.setEnabled(ready);
        String m = effectiveMuted() ? "Unmute" : "Mute"; mute.setText(m); mute.setContentDescription(m);
        rotation.setText(locked ? "Rotation locked" : "Auto rotate");
        rotation.setContentDescription(locked ? "Rotation locked" : "Auto rotate");
    }
    private void fitVideo() {
        if (video == null || picture == null || width <= 0 || height <= 0) return;
        int availableW = picture.getWidth(), availableH = picture.getHeight();
        if (availableW <= 0 || availableH <= 0) return;
        double scale = filling ? Math.max((double)availableW/width, (double)availableH/height)
                : Math.min((double)availableW/width, (double)availableH/height);
        int w = Math.max(1,(int)Math.round(width*scale)), h = Math.max(1,(int)Math.round(height*scale));
        FrameLayout.LayoutParams old = (FrameLayout.LayoutParams)video.getLayoutParams();
        if (old.width != w || old.height != h) video.setLayoutParams(new FrameLayout.LayoutParams(w,h,Gravity.CENTER));
    }
    private String time(int value) {
        int seconds = Math.max(0,value)/1000;
        return String.format(Locale.ROOT, "%d:%02d", seconds/60, seconds%60);
    }
}
