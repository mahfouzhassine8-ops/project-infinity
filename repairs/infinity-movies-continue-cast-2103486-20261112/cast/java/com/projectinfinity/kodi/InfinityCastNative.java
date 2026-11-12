package com.projectinfinity.kodi;

/** Cast-only JNI. Requests run on Kodi's existing GUI queue and fail closed. */
final class InfinityCastNative {
    private InfinityCastNative() {}
    static native long request(String operation, String token, long positionMs);
    static native byte[] poll(long request);
    /** True only if cancellation preceded native command commitment. */
    static native boolean cancel(long request);
}
