package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import java.lang.ref.WeakReference;
import java.util.Locale;

/** The shell's only external-video edge: no Kodi/Cobra runtime dependency. */
public final class ExternalVideoRoute {
    private ExternalVideoRoute() {}
    private static final java.util.WeakHashMap<Activity,Intent> pending = new java.util.WeakHashMap<>();

    public static boolean captures(Activity splash, Intent intent) {
        return intent != null && (pending.containsKey(splash) || accepts(intent));
    }
    public static void stage(Activity splash, Intent intent) {
        // Do not finish inside an Android launch/new-intent transaction. Other
        // requests already queued for this singleInstance gateway must be
        // delivered first. One main-queue handoff consumes their latest value;
        // there is no timer, polling, additional thread or parallel player.
        boolean queued = pending.containsKey(splash);
        pending.put(splash, new Intent(intent));
        if (queued) return;
        WeakReference<Activity> owner = new WeakReference<>(splash);
        new Handler(Looper.getMainLooper()).post(() -> {
            Activity gateway = owner.get();
            if (gateway == null) return;
            Intent latest = pending.remove(gateway);
            if (latest != null && !gateway.isFinishing() && !gateway.isDestroyed())
                open(gateway, latest);
        });
    }

    public static boolean accepts(Intent intent) {
        if (intent == null) return false;
        try {
            boolean send = Intent.ACTION_SEND.equals(intent.getAction());
            if (!send && !Intent.ACTION_VIEW.equals(intent.getAction())) return false;
            Uri uri = send ? intent.getParcelableExtra(Intent.EXTRA_STREAM) : intent.getData();
            if (uri == null || uri.getScheme() == null) return false;
            String type = intent.getType();
            if (type != null) type = type.toLowerCase(Locale.ROOT).split(";", 2)[0].trim();
            if (type != null && (type.startsWith("video/")
                    || type.equals("application/vnd.apple.mpegurl")
                    || type.equals("application/x-mpegurl"))) return true;
            if (send || (type != null && !type.equals("application/octet-stream"))) return false;
            String path = uri.getPath();
            return path != null && path.toLowerCase(Locale.ROOT)
                    .matches(".*\\.(mp4|m4v|mkv|webm|mov|3gp|ts|m2ts|avi|mpeg|mpg|m3u8)$");
        } catch (RuntimeException malformed) { return false; }
    }

    public static void open(Activity splash, Intent incoming) {
        try {
        // A copy retains ClipData, MIME, URI grants and source-provided extras.
        Intent next = new Intent(incoming);
        int grants = incoming.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        if (!accepts(incoming)) {
            // A normal request superseded the queued video. This
            // gateway has not initialized the chooser; let the original entry
            // perform its ordinary onCreate with the original action/extras.
            next.setClassName(splash.getPackageName(), "com.projectinfinity.kodi.Splash");
            next.setFlags(grants | Intent.FLAG_ACTIVITY_NEW_TASK);
            splash.finish(); splash.startActivity(next); return;
        }
        Uri uri = Intent.ACTION_SEND.equals(incoming.getAction())
                ? incoming.getParcelableExtra(Intent.EXTRA_STREAM) : incoming.getData();
        next.setAction(Intent.ACTION_VIEW);
        next.setDataAndType(uri, incoming.getType());
        next.setClassName(splash.getPackageName(),
                "com.projectinfinity.kodi.InfinityExternalPlayerActivity");
        next.setSelector(null);
        // Never propagate arbitrary task clearing, document, multiple-task or
        // launch-adjacent flags into the private single-session player.
        next.setFlags(grants | Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        if (next.getClipData() == null && uri != null && "content".equals(uri.getScheme()))
            next.setClipData(ClipData.newRawUri("Video", uri));
        // Preserve source extras but replace caller-controlled private identity.
        next.putExtra("infinity.external.request", java.util.UUID.randomUUID().toString());
        splash.startActivity(next);
        }
        catch (RuntimeException unavailable) {
            android.widget.Toast.makeText(splash, "Unable to open the external video player.",
                    android.widget.Toast.LENGTH_LONG).show();
        }
        // Finish only this gateway; never finishAffinity, stop a service or call Kodi.
        finally { splash.finish(); }
    }
}
