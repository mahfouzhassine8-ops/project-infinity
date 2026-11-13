package com.projectinfinity.kodi;

import java.io.IOException;

/** Cast-only JNI. The existing Kodi/FFmpeg engine must already be loaded. */
final class InfinityCastRemuxNative {
    private static boolean loaded;
    static synchronized void load() throws IOException {
        if(loaded)return;
        try{System.loadLibrary("infinitycastremux");loaded=true;}
        catch(LinkageError unavailable){throw new IOException("mkv_native_library_unavailable");}
    }
    static native long open(Object input) throws IOException;
    static native String inspect(long handle) throws IOException;
    static native byte[] init(long handle) throws IOException;
    static native byte[] segment(long handle,int index) throws IOException;
    static native void cancel(long handle);
    static native void close(long handle);
    static native int active();
}
