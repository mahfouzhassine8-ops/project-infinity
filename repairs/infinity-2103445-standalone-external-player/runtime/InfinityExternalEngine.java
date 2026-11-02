package com.projectinfinity.kodi;

import android.content.Context;
import android.content.Intent;
import android.content.res.AssetFileDescriptor;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** All decoder/provider operations belong to this worker, never the UI thread. */
public final class InfinityExternalEngine {
    public interface Observer {
        void event(String event, String detail);
        void position(int position, int duration);
        void size(int width, int height);
        void tracks(String[] labels, int[] indexes, int selected, boolean subtitles);
        void subtitle(String text);
    }
    private final Context context;
    private final Observer observer;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final HandlerThread thread = new HandlerThread("InfinityExternalDecoder");
    private final Handler worker;
    private volatile long epoch;
    private volatile boolean destroyed;
    private MediaPlayer player;
    private volatile boolean prepared;
    private boolean buffering;
    private Runnable deadline;
    private Runnable ticker;
    private float volume = 1f;
    private android.view.Surface surface;
    private long startPosition;
    private final InfinityExternalResume resume;
    private InfinityExternalResume.Identity identity;
    private InfinityExternalResume.Entry memory;
    private boolean remember, choosingResume, seekingResume, initialSeek, seekable = true, resumeWarning;
    private long lastCheckpoint;
    private static final int PREPARE_LIMIT_MS = 45000;

    public InfinityExternalEngine(Context context, Observer observer) {
        this.context = context.getApplicationContext(); this.observer = observer;
        resume = new InfinityExternalResume(this.context);
        thread.start(); worker = new Handler(thread.getLooper());
    }
    private boolean current(long id, MediaPlayer p) { return !destroyed && epoch == id && player == p; }
    private void emit(long id, String event, String detail) {
        ui.post(() -> { if (!destroyed && epoch == id) observer.event(event, detail); });
    }
    public void open(Intent request, long position, boolean offerResume) {
        final long id = ++epoch;
        if (deadline != null) ui.removeCallbacks(deadline);
        final Intent copy = new Intent(request);
        worker.post(() -> {
            if (destroyed || epoch != id) return;
            releasePlayer();
            MediaPlayer p = new MediaPlayer(); player = p; startPosition = Math.max(0, position);
            emit(id, "opening", "");
            p.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MOVIE).build());
            p.setVolume(volume, volume);
            p.setSurface(surface);
            p.setOnPreparedListener(mp -> {
                if (!current(id, mp)) return;
                if (deadline != null) ui.removeCallbacks(deadline);
                boolean hasVideo = false;
                for (MediaPlayer.TrackInfo track : mp.getTrackInfo())
                    if (track.getTrackType() == MediaPlayer.TrackInfo.MEDIA_TRACK_TYPE_VIDEO) hasVideo = true;
                if (!hasVideo) { emit(id, "error", "This source has no supported video track."); releasePlayer(); return; }
                prepared = true;
                if (identity != null && seekable && mp.getDuration() > 0) try {
                    memory = resume.load(identity, mp.getDuration());
                } catch (RuntimeException unavailable) { historyUnavailable(id); }
                choosingResume = offerResume && memory != null && memory.position > 0;
                remember = !choosingResume;
                if (choosingResume) emit(id, "resume", Long.toString(memory.position));
                // A lifecycle checkpoint can precede its queued UI position
                // callback. The committed decoder position is authoritative.
                if (!offerResume && memory != null && memory.position > 0) startPosition = memory.position;
                if (!choosingResume && startPosition > 0) {
                    initialSeek = true;
                    beginSeek(id, mp, startPosition);
                } else emit(id, "ready", "");
                postSize(id, mp.getVideoWidth(), mp.getVideoHeight());
                position(id, mp);
            });
            p.setOnInfoListener((mp, what, extra) -> {
                if (!current(id, mp)) return true;
                if (what == MediaPlayer.MEDIA_INFO_VIDEO_RENDERING_START) emit(id, "frame", "");
                if (what == MediaPlayer.MEDIA_INFO_BUFFERING_START) {
                    buffering = true; emit(id, "buffering", "");
                }
                if (what == MediaPlayer.MEDIA_INFO_BUFFERING_END) {
                    buffering = false; emit(id, mp.isPlaying() ? "playing" : "paused", "");
                }
                if (what == MediaPlayer.MEDIA_INFO_NOT_SEEKABLE) {
                    seekable = false; remember = false; emit(id, "not_seekable", "");
                    if (choosingResume) { choosingResume = false; emit(id, "resume_unavailable", ""); }
                }
                return true;
            });
            p.setOnVideoSizeChangedListener((mp, width, height) -> {
                if (current(id, mp)) postSize(id, width, height);
            });
            p.setOnCompletionListener(mp -> {
                if (current(id, mp)) {
                    remember = false; clearMemory(id); position(id, mp); emit(id, "ended", "");
                }
            });
            p.setOnSeekCompleteListener(mp -> {
                if (current(id, mp) && seekingResume) {
                    seekingResume = false; remember = true;
                    if (deadline != null) { ui.removeCallbacks(deadline); deadline = null; }
                    checkpoint(); position(id, mp);
                    emit(id, initialSeek ? "ready" : "resume_ready", ""); initialSeek = false;
                }
            });
            p.setOnErrorListener((mp, what, extra) -> {
                if (current(id, mp)) {
                    emit(id, "error", "This video cannot be played. Check access, connection and format ("
                            + what + "/" + extra + ").");
                    releasePlayer();
                }
                return true;
            });
            p.setOnTimedTextListener((mp, text) -> {
                if (current(id, mp)) ui.post(() -> {
                    if (!destroyed && epoch == id) observer.subtitle(text == null ? "" : text.getText());
                });
            });
            // Timeout belongs to this request. It reports failure, never readiness.
            // It also leaves Close/Back usable while a document provider is slow.
            deadline = () -> {
                if (!destroyed && epoch == id && !prepared) {
                    final long canceled = ++epoch;
                    observer.event("error", "The source did not become ready. Check the connection or reopen it from the source app.");
                    worker.post(() -> { if (epoch == canceled) releasePlayer(); });
                }
            };
            ui.postDelayed(deadline, PREPARE_LIMIT_MS);
            try {
                Uri uri = copy.getData();
                if (uri == null || uri.getScheme() == null) throw new IllegalArgumentException("Missing video URI");
                String scheme = uri.getScheme().toLowerCase(Locale.ROOT);
                if (scheme.equals("content")) {
                    String authority = uri.getAuthority();
                    if ("com.projectinfinity.kodi.media".equals(authority)
                            || "com.projectinfinity.kodi.file".equals(authority)
                            || "com.projectinfinity.kodi.ytdl".equals(authority))
                        throw new IllegalArgumentException("A Kodi-owned provider cannot be opened independently");
                    // Use a granted descriptor directly, preserving offset/length.
                    // Never convert a provider URI to a guessed /storage path.
                    try (AssetFileDescriptor fd = context.getContentResolver().openAssetFileDescriptor(uri, "r")) {
                        if (fd == null) throw new java.io.FileNotFoundException();
                        identify(id, uri, fd.getFileDescriptor(), fd.getStartOffset(), fd.getDeclaredLength());
                        if (fd.getDeclaredLength() < 0) p.setDataSource(fd.getFileDescriptor());
                        else p.setDataSource(fd.getFileDescriptor(), fd.getStartOffset(), fd.getDeclaredLength());
                    }
                } else if (scheme.equals("file")) {
                    p.setDataSource(context, uri);
                    try (AssetFileDescriptor fd = context.getContentResolver().openAssetFileDescriptor(uri, "r")) {
                        identify(id, uri, fd == null ? null : fd.getFileDescriptor(), 0, -1);
                    } catch (Exception inaccessibleMetadata) { identify(id, uri, null, 0, -1); }
                } else if (scheme.equals("http") || scheme.equals("https")) {
                    identify(id, uri, null, 0, -1);
                    p.setDataSource(context, uri, headers(copy));
                } else throw new IllegalArgumentException("Unsupported video protocol");
                if (!current(id, p)) { releasePlayer(); return; }
                emit(id, "preparing", ""); p.prepareAsync();
            } catch (Exception failure) {
                if (current(id, p)) {
                    emit(id, "error", failure instanceof SecurityException
                            ? "Access to this video was not granted. Reopen it from the source app."
                            : "Unable to open this video. Check access, protocol and supported format.");
                    releasePlayer();
                }
            }
        });
    }
    private void identify(long id, Uri uri, java.io.FileDescriptor fd, long offset, long length) {
        try { identity = resume.identify(uri, fd, offset, length); }
        catch (RuntimeException unavailable) { identity = null; historyUnavailable(id); }
    }
    private void historyUnavailable(long id) {
        if (!resumeWarning) { resumeWarning = true; emit(id, "history_unavailable", "Resume memory is unavailable. Playback can continue."); }
    }
    private void clearMemory(long id) {
        try { resume.clear(memory); } catch (RuntimeException unavailable) { historyUnavailable(id); }
    }
    private void checkpoint() {
        if (!prepared || player == null || !remember || !seekable || memory == null) return;
        try {
            resume.save(memory, player.getCurrentPosition());
            lastCheckpoint = android.os.SystemClock.elapsedRealtime();
        } catch (RuntimeException unavailable) { historyUnavailable(epoch); }
    }
    public void chooseResume(boolean restore) { command(p -> {
        if (!choosingResume || memory == null) return;
        choosingResume = false;
        if (!restore) clearMemory(epoch);
        beginSeek(epoch, p, restore ? memory.position : 0);
    }); }
    private void beginSeek(long id, MediaPlayer p, long target) {
        seekingResume = true; remember = false;
        // Ready is emitted only by actual seek completion, never this deadline.
        deadline = () -> {
            if (!destroyed && epoch == id) {
                final long canceled = ++epoch;
                observer.event("error", "The resume seek did not complete. Reopen the video to retry or start over.");
                worker.post(() -> { if (epoch == canceled) releasePlayer(); });
            }
        };
        ui.postDelayed(deadline, PREPARE_LIMIT_MS);
        if (android.os.Build.VERSION.SDK_INT >= 26) p.seekTo(target, MediaPlayer.SEEK_CLOSEST);
        else p.seekTo((int)Math.min(target, Integer.MAX_VALUE));
    }
    private Map<String,String> headers(Intent intent) {
        Map<String,String> result = new HashMap<>();
        Bundle supplied = intent.getBundleExtra("android.media.intent.extra.HTTP_HEADERS");
        if (supplied != null) for (String key : supplied.keySet()) {
            Object value = supplied.get(key);
            if (value instanceof String && !key.contains("\r") && !key.contains("\n")
                    && !((String)value).contains("\r") && !((String)value).contains("\n"))
                result.put(key, (String)value);
        }
        return result;
    }
    private void postSize(long id, int width, int height) {
        ui.post(() -> { if (!destroyed && epoch == id) observer.size(width, height); });
    }
    private void position(long id, MediaPlayer p) {
        if (!current(id, p) || !prepared) return;
        int now = p.getCurrentPosition(), duration = p.getDuration();
        ui.post(() -> { if (!destroyed && epoch == id) observer.position(now, duration); });
    }
    private void tick(long id, MediaPlayer p) {
        if (!current(id, p) || !prepared) return;
        try {
            position(id, p);
            if (android.os.SystemClock.elapsedRealtime() - lastCheckpoint >= InfinityExternalResume.INTERVAL) checkpoint();
            if (p.isPlaying() && ticker != null) worker.postDelayed(ticker, 500);
        } catch (IllegalStateException invalid) { emit(id, "error", "Playback is no longer available. Reopen the video."); }
    }
    public void play() { command(p -> {
        if (choosingResume || seekingResume) return;
        remember = true;
        if (ticker != null) worker.removeCallbacks(ticker);
        final long id = epoch; ticker = () -> tick(id, p);
        p.start(); emit(id, buffering ? "buffering" : "playing", ""); ticker.run();
    }); }
    public void pause() { command(p -> {
        if (choosingResume || seekingResume) return;
        if (ticker != null) worker.removeCallbacks(ticker);
        p.pause(); checkpoint(); position(epoch, p); emit(epoch, "paused", "");
    }); }
    public void seek(int ms) { command(p -> { p.seekTo(Math.max(0, ms)); }); }
    private interface Operation { void run(MediaPlayer player); }
    private void command(Operation operation) {
        final long id = epoch;
        worker.post(() -> {
            if (destroyed || id != epoch || player == null || !prepared) return;
            try { operation.run(player); }
            catch (RuntimeException invalid) { emit(id, "error", "The playback operation is unavailable for this source."); }
        });
    }
    public void volume(float value) {
        worker.post(() -> { volume = Math.max(0, Math.min(1, value)); if (player != null) player.setVolume(volume, volume); });
    }
    public void surface(android.view.Surface value) {
        worker.post(() -> { surface = value; if (player != null) player.setSurface(value); });
    }
    public void listTracks(boolean subtitles) {
        command(p -> {
            MediaPlayer.TrackInfo[] tracks = p.getTrackInfo();
            ArrayList<String> labels = new ArrayList<>(); ArrayList<Integer> indexes = new ArrayList<>();
            int type = subtitles ? MediaPlayer.TrackInfo.MEDIA_TRACK_TYPE_TIMEDTEXT : MediaPlayer.TrackInfo.MEDIA_TRACK_TYPE_AUDIO;
            int current = p.getSelectedTrack(type);
            if (subtitles) { labels.add("Off"); indexes.add(-1); }
            for (int i = 0; i < tracks.length; i++) if (tracks[i].getTrackType() == type) {
                labels.add((subtitles ? "Subtitle " : "Audio ") + (labels.size() + (subtitles ? 0 : 1))
                        + " · " + tracks[i].getLanguage()); indexes.add(i);
            }
            String[] names = labels.toArray(new String[0]); int[] values = new int[indexes.size()];
            for (int i = 0; i < values.length; i++) values[i] = indexes.get(i);
            final long id = epoch;
            ui.post(() -> { if (!destroyed && id == epoch) observer.tracks(names, values, current, subtitles); });
        });
    }
    public void selectTrack(int index, boolean subtitles) {
        command(p -> {
            if (index >= 0) p.selectTrack(index);
            else if (subtitles) {
                int selected = p.getSelectedTrack(MediaPlayer.TrackInfo.MEDIA_TRACK_TYPE_TIMEDTEXT);
                if (selected >= 0) p.deselectTrack(selected);
            }
        });
    }
    public void suspend() { ++epoch; worker.post(this::releasePlayer); }
    private void releasePlayer() {
        checkpoint();
        if (deadline != null) { ui.removeCallbacks(deadline); deadline = null; }
        if (ticker != null) { worker.removeCallbacks(ticker); ticker = null; }
        prepared = false; buffering = false;
        identity = null; memory = null; remember = choosingResume = seekingResume = initialSeek = false;
        seekable = true; resumeWarning = false; lastCheckpoint = 0;
        if (player != null) { player.setOnErrorListener(null); player.release(); player = null; }
    }
    public void destroy() {
        destroyed = true; ++epoch; ui.removeCallbacksAndMessages(null);
        worker.post(() -> { releasePlayer(); resume.close(); surface = null; thread.quitSafely(); });
    }
}
