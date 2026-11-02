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

/** Private external-video UI. Has no Kodi/Cobra/service/persistence dependencies. */
public final class InfinityExternalPlayerActivity extends Activity implements InfinityExternalEngine.Observer {
    private final InfinityExternalState state = new InfinityExternalState();
    private InfinityExternalEngine engine;
    private long token;
    private FrameLayout root, picture;
    private SurfaceView video;
    private LinearLayout controls, top, notice;
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
    private String requestId;
    private final AudioManager.OnAudioFocusChangeListener focus = change -> runOnUiThread(() -> {
        if (engine == null || isFinishing()) return;
        if (change == AudioManager.AUDIOFOCUS_GAIN) {
            focusHeld = true;
            if (focusResume && started) { focusResume = false; wantsPlay = true; startPlayback(); }
        } else if (change == AudioManager.AUDIOFOCUS_LOSS || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT
                || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK) {
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
        buildUi(); accept(getIntent(), saved != null);
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
        token = next; requestId = id; ready = false;
        setIntent(request);
        if (!restored) { position = 0; wantsPlay = true; }
        duration = 0; width = height = 0; subtitles.setText(""); seek.setProgress(0); seek.setEnabled(false);
        String name = request != null && request.getData() != null ? request.getData().getLastPathSegment() : null;
        title.setText(name == null || name.isEmpty() ? "Infinity video" : name);
        if (started) load();
    }
    @Override protected void onNewIntent(Intent intent) { super.onNewIntent(intent); accept(intent, false); }
    private void load() {
        ready = false; state.set(token, InfinityExternalState.Phase.OPENING); showStatus("Loading…", true);
        engine.volume(muted ? 0f : level); engine.open(getIntent(), position); updateButtons();
    }
    @Override protected void onStart() { super.onStart(); started = true; load(); }
    @Override protected void onPause() {
        engine.pause(); abandonFocus(); super.onPause();
    }
    @Override protected void onStop() {
        started = false; ready = false; engine.suspend(); abandonFocus();
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); super.onStop();
    }
    @Override protected void onDestroy() { state.release(); engine.destroy(); abandonFocus(); super.onDestroy(); }
    @Override protected void onSaveInstanceState(Bundle out) {
        out.putInt("position", position); out.putBoolean("muted", muted); out.putBoolean("play", wantsPlay);
        out.putFloat("level", level); out.putBoolean("fill", filling); out.putBoolean("locked", locked);
        super.onSaveInstanceState(out);
    }
    @Override public void onConfigurationChanged(Configuration config) { super.onConfigurationChanged(config); fitVideo(); }
    @Override public void onBackPressed() { close(); }
    private void close() {
        wantsPlay = false; state.release(); engine.suspend(); abandonFocus(); finish();
    }
    private boolean obtainFocus() {
        if (muted || focusHeld) return true;
        int result;
        if (Build.VERSION.SDK_INT >= 26) {
            focusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
                    .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MOVIE).build())
                    .setOnAudioFocusChangeListener(focus).build();
            result = audio.requestAudioFocus(focusRequest);
        } else result = audio.requestAudioFocus(focus, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT);
        focusHeld = result == AudioManager.AUDIOFOCUS_REQUEST_GRANTED; return focusHeld;
    }
    private void abandonFocus() {
        focusResume = false;
        if (focusRequest != null && Build.VERSION.SDK_INT >= 26) audio.abandonAudioFocusRequest(focusRequest);
        else if (audio != null && focusHeld) audio.abandonAudioFocus(focus);
        focusRequest = null; focusHeld = false;
    }
    private void startPlayback() {
        if (!ready || !started || !wantsPlay) return;
        if (!obtainFocus()) { wantsPlay = false; showStatus("Audio is in use. Press Play to retry.", false); updateButtons(); return; }
        engine.play();
    }
    @Override public void event(String event, String detail) {
        if (!started || isFinishing()) return;
        android.util.Log.i("InfinityExternalPlayer", event); // No private URI, title, headers or source extras.
        switch (event) {
            case "opening": state.set(token, InfinityExternalState.Phase.OPENING); showStatus("Loading…", true); break;
            case "preparing": state.set(token, InfinityExternalState.Phase.PREPARING); showStatus("Loading…", true); break;
            case "ready":
                ready = true; state.set(token, InfinityExternalState.Phase.READY); showStatus("", false);
                if (wantsPlay) startPlayback(); else event("paused", ""); break;
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
                ready = false; wantsPlay = false; state.set(token, InfinityExternalState.Phase.ERROR);
                showStatus(detail, false); abandonFocus();
                getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); break;
            case "not_seekable": seek.setEnabled(false); break;
        }
        updateButtons();
    }
    @Override public void position(int now, int total) {
        position = now; duration = total;
        times.setText(time(now) + " / " + (total > 0 ? time(total) : "Live"));
        seek.setEnabled(ready && total > 0);
        if (!dragging) { seek.setMax(Math.max(total, 1)); seek.setProgress(Math.max(0, now)); }
    }
    @Override public void size(int w, int h) { width = w; height = h; fitVideo(); }
    @Override public void subtitle(String text) { subtitles.setText(text); }
    @Override public void tracks(String[] labels, int[] indexes, int selected, boolean caption) {
        if (isFinishing() || !started) return;
        if (labels.length == 0 || (caption && labels.length == 1)) {
            new AlertDialog.Builder(this).setTitle(caption ? "Subtitles" : "Audio")
                    .setMessage(caption ? "No supported text subtitle tracks in this video." : "No selectable audio tracks in this video.")
                    .setPositiveButton("OK", null).show(); return;
        }
        int checked = -1;
        for (int i = 0; i < indexes.length; i++) if (indexes[i] == selected) checked = i;
        new AlertDialog.Builder(this).setTitle(caption ? "Subtitles" : "Audio")
                .setSingleChoiceItems(labels, checked, (dialog, which) -> {
                    engine.selectTrack(indexes[which], caption); if (caption) subtitles.setText(""); dialog.dismiss();
                }).setNegativeButton("Cancel", null).show();
    }
    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }
    private TextView text(int sp) {
        TextView t = new TextView(this); t.setTextColor(Color.WHITE); t.setTextSize(sp); return t;
    }
    private Button button(String label, Runnable click) {
        Button b = new Button(this); b.setAllCaps(false); b.setText(label); b.setContentDescription(label);
        b.setTextColor(Color.WHITE); b.setTextSize(14); b.setMinHeight(dp(48)); b.setMinWidth(dp(64));
        GradientDrawable surface = new GradientDrawable(); surface.setColor(0xe6172634);
        surface.setCornerRadius(dp(10)); surface.setStroke(dp(1), 0xff29c3d8); b.setBackground(surface);
        b.setPadding(dp(12), dp(6), dp(12), dp(6)); b.setOnClickListener(v -> click.run()); return b;
    }
    private void buildUi() {
        getWindow().setStatusBarColor(Color.BLACK); getWindow().setNavigationBarColor(Color.BLACK);
        root = new FrameLayout(this); root.setBackgroundColor(Color.BLACK); setContentView(root);
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom()); return insets;
        });
        picture = new FrameLayout(this); root.addView(picture, new FrameLayout.LayoutParams(-1, -1));
        video = new SurfaceView(this); picture.addView(video, new FrameLayout.LayoutParams(-1, -1, Gravity.CENTER));
        video.getHolder().addCallback(new SurfaceHolder.Callback() {
            public void surfaceCreated(SurfaceHolder h) { engine.surface(h.getSurface()); }
            public void surfaceChanged(SurfaceHolder h, int format, int w, int he) { engine.surface(h.getSurface()); }
            public void surfaceDestroyed(SurfaceHolder h) { engine.surface(null); }
        });
        picture.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob) -> { if (r-l != or-ol || b-t != ob-ot) fitVideo(); });
        video.setOnClickListener(v -> {
            boolean visible = controls.getVisibility() == View.VISIBLE;
            controls.setVisibility(visible ? View.GONE : View.VISIBLE); top.setVisibility(visible ? View.GONE : View.VISIBLE);
        });
        subtitles = text(20); subtitles.setGravity(Gravity.CENTER); subtitles.setShadowLayer(3,1,1,Color.BLACK);
        FrameLayout.LayoutParams subtitleParams = new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM);
        subtitleParams.bottomMargin = dp(150); root.addView(subtitles, subtitleParams);
        top = new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL); top.setBackgroundColor(0xa0000000);
        top.addView(button("Close", this::close)); title = text(16); title.setMaxLines(1);
        title.setEllipsize(android.text.TextUtils.TruncateAt.MIDDLE); title.setPadding(dp(12),0,dp(8),0);
        top.addView(title, new LinearLayout.LayoutParams(0,dp(52),1));
        root.addView(top, new FrameLayout.LayoutParams(-1,-2,Gravity.TOP));
        notice = new LinearLayout(this); notice.setOrientation(LinearLayout.VERTICAL); notice.setGravity(Gravity.CENTER);
        notice.setPadding(dp(20),dp(12),dp(20),dp(12));
        busy = new ProgressBar(this); busy.setIndeterminateTintList(android.content.res.ColorStateList.valueOf(0xff29c3d8));
        notice.addView(busy,new LinearLayout.LayoutParams(dp(32),dp(32)));
        message = text(16); message.setGravity(Gravity.CENTER); notice.addView(message);
        retry = button("Retry", () -> { wantsPlay = true; load(); }); notice.addView(retry);
        root.addView(notice,new FrameLayout.LayoutParams(-1,-2,Gravity.CENTER));
        controls = new LinearLayout(this); controls.setOrientation(LinearLayout.VERTICAL); controls.setBackgroundColor(0xd9000000);
        controls.setPadding(dp(8),dp(4),dp(8),dp(8)); times = text(13); controls.addView(times);
        seek = new SeekBar(this); seek.setContentDescription("Seek video"); controls.addView(seek,new LinearLayout.LayoutParams(-1,dp(40)));
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onStartTrackingTouch(SeekBar s) { dragging = true; }
            public void onProgressChanged(SeekBar s,int value,boolean user) { if (user) times.setText(time(value)+" / "+time(duration)); }
            public void onStopTrackingTouch(SeekBar s) { dragging = false; engine.seek(s.getProgress()); }
        });
        HorizontalScrollView strip = new HorizontalScrollView(this); strip.setHorizontalScrollBarEnabled(false);
        LinearLayout row = new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL); strip.addView(row);
        play = button("Pause", () -> {
            wantsPlay = !wantsPlay;
            if (wantsPlay) {
                if (state.phase() == InfinityExternalState.Phase.ENDED) { position = 0; engine.seek(0); }
                startPlayback();
            } else { engine.pause(); abandonFocus(); }
            updateButtons();
        }); row.addView(play);
        row.addView(button("Stop", this::close));
        row.addView(button("−10 s", () -> engine.seek(Math.max(0, position-10000))));
        row.addView(button("+10 s", () -> engine.seek(duration > 0 ? Math.min(duration,position+10000) : position+10000)));
        mute = button("Mute", () -> {
            muted = !muted; engine.volume(muted ? 0 : level);
            if (muted) abandonFocus(); else if (!obtainFocus()) { muted = true; engine.volume(0); }
            updateButtons();
        }); row.addView(mute);
        row.addView(button("Volume", () -> {
            SeekBar volume = new SeekBar(this); volume.setMax(100); volume.setProgress(Math.round(level*100));
            volume.setContentDescription("Player volume");
            volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onStartTrackingTouch(SeekBar s) {}
                public void onStopTrackingTouch(SeekBar s) {}
                public void onProgressChanged(SeekBar s,int value,boolean user) {
                    if (user) { level = value/100f; engine.volume(muted ? 0 : level); }
                }
            });
            new AlertDialog.Builder(this).setTitle("Player volume").setView(volume).setPositiveButton("Done",null).show();
        }));
        row.addView(button("Audio", () -> engine.listTracks(false)));
        row.addView(button("Subtitles", () -> engine.listTracks(true)));
        row.addView(button("Display", () -> new AlertDialog.Builder(this).setTitle("Display")
                .setSingleChoiceItems(new String[]{"Best Fit", "Fill (crop)"}, filling ? 1 : 0, (d,which) -> {
                    filling = which == 1; fitVideo(); d.dismiss();
                }).setNegativeButton("Cancel",null).show()));
        rotation = button("Auto rotate", () -> {
            locked = !locked;
            setRequestedOrientation(locked ? android.content.pm.ActivityInfo.SCREEN_ORIENTATION_LOCKED
                    : android.content.pm.ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR); updateButtons();
        }); row.addView(rotation);
        for (int i=0; i<row.getChildCount(); i++) {
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-2,dp(48)); p.setMargins(dp(3),0,dp(3),0); row.getChildAt(i).setLayoutParams(p);
        }
        controls.addView(strip); root.addView(controls,new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM));
        root.requestApplyInsets(); updateButtons();
    }
    private void showStatus(String text, boolean loading) {
        message.setText(text); busy.setVisibility(loading ? View.VISIBLE : View.GONE);
        retry.setVisibility(state.phase() == InfinityExternalState.Phase.ERROR ? View.VISIBLE : View.GONE);
        notice.setVisibility(text.isEmpty() ? View.GONE : View.VISIBLE);
    }
    private void updateButtons() {
        if (play == null) return;
        String p = wantsPlay ? "Pause" : "Play"; play.setText(p); play.setContentDescription(p); play.setEnabled(ready);
        String m = muted ? "Unmute" : "Mute"; mute.setText(m); mute.setContentDescription(m);
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
