/* SPDX-License-Identifier: GPL-2.0-or-later
 * G2 Candidate 6: hardened upper-layer adapter on the exact working G2 #5 ABI.
 */
package com.projectinfinity.kodi;

import android.app.PictureInPictureParams;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Looper;
import android.util.Log;
import android.util.Rational;

public final class InfinityCoreBridge {
    private static final int EXPECTED_NATIVE_VERSION = 2;
    private static final String TAG = "InfinityG2Mapping";
    private InfinityCoreBridge() {}

    public static int getBridgeVersion(Main activity) {
        if (activity == null) return 0;
        try { return activity._infinityBridgeVersion(); }
        catch (LinkageError error) { Log.w(TAG, "Native bridge unavailable", error); return 0; }
    }

    private static boolean compatible(Main activity) {
        return activity != null && getBridgeVersion(activity) == EXPECTED_NATIVE_VERSION;
    }

    public static boolean hasActiveVideoPlayer(Main activity) {
        if (!compatible(activity)) return false;
        try { return activity._infinityHasActiveVideo(); }
        catch (LinkageError error) { Log.w(TAG, "Video-state bridge unavailable", error); return false; }
    }

    public static void syncDisplayState(Main activity) {
        if (!compatible(activity)) return;
        try { activity._infinitySyncDisplayState(); }
        catch (LinkageError error) { Log.w(TAG, "Display bridge unavailable", error); }
    }

    public static int getSystemThemeMode(Main activity) {
        if (!compatible(activity)) return 0;
        try { return activity._infinitySystemThemeMode(); }
        catch (LinkageError error) { Log.w(TAG, "Theme-state bridge unavailable", error); return 0; }
    }

    public static int getNativeWindowWidth(Main activity) {
        if (!compatible(activity)) return -1;
        try { return activity._infinityWindowWidth(); }
        catch (LinkageError error) { Log.w(TAG, "Window-width bridge unavailable", error); return -1; }
    }

    public static int getNativeWindowHeight(Main activity) {
        if (!compatible(activity)) return -1;
        try { return activity._infinityWindowHeight(); }
        catch (LinkageError error) { Log.w(TAG, "Window-height bridge unavailable", error); return -1; }
    }

    private static boolean canUsePip(Main activity) {
        return Build.VERSION.SDK_INT >= 26 && activity != null
                && Looper.myLooper() == Looper.getMainLooper()
                && !activity.isFinishing() && !activity.isDestroyed()
                && activity.getPackageManager().hasSystemFeature(PackageManager.FEATURE_PICTURE_IN_PICTURE)
                && compatible(activity);
    }

    public static void updateInfinityPictureInPictureParams(Main activity) {
        try {
            if (!canUsePip(activity)) return;
            PictureInPictureParams.Builder builder = new PictureInPictureParams.Builder().setAspectRatio(new Rational(16, 9));
            if (Build.VERSION.SDK_INT >= 31) builder.setAutoEnterEnabled(false);
            activity.setPictureInPictureParams(builder.build());
        } catch (IllegalArgumentException | IllegalStateException | SecurityException error) {
            Log.w(TAG, "Android rejected PiP parameters", error);
        } catch (LinkageError error) {
            Log.w(TAG, "PiP API unavailable", error);
        }
    }

    public static boolean enterInfinityPictureInPicture(Main activity) {
        try {
            if (!canUsePip(activity) || activity.isInPictureInPictureMode() || !hasActiveVideoPlayer(activity)) return false;
            PictureInPictureParams params = new PictureInPictureParams.Builder().setAspectRatio(new Rational(16, 9)).build();
            return activity.enterPictureInPictureMode(params);
        } catch (IllegalArgumentException | IllegalStateException | SecurityException error) {
            Log.w(TAG, "Android rejected PiP entry", error);
            return false;
        } catch (LinkageError error) {
            Log.w(TAG, "PiP API unavailable", error);
            return false;
        }
    }
}
