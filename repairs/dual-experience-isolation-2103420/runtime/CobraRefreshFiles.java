package com.projectinfinity.kodi;

import android.content.Context;
import java.io.*;
import java.nio.channels.FileLock;

/** Lossless first-use snapshot of Cobra's previously shared refresh files.
 * The original Infinity files remain in place and are never written here.
 * Each storage root has its own durable completion marker, so temporary
 * external-storage unavailability does not lose the later external profile.
 */
public final class CobraRefreshFiles {
  private static final Object LOCK=new Object();
  private CobraRefreshFiles() {}
  public static File directory(Context context) {
    synchronized(LOCK) {
      File base=context.getExternalFilesDir(null);if(base==null)base=context.getFilesDir();
      File own=new File(base,".cobra/refresh");
      File marker=new File(own,"isolation-v1.ready");
      if(marker.isFile())return own;
      try {
        if(!own.isDirectory()&&!CobraJavaPersistence.mkdirs(own))throw new IOException("Cobra refresh directory unavailable");
        try(RandomAccessFile guard=new RandomAccessFile(new File(own,"isolation-v1.lock"),"rw");FileLock held=guard.getChannel().lock()) {
          if(marker.isFile())return own;
          File original=new File(base,".kodi/userdata/addon_data/service.infinity.refresh");
          copyIfMissing(new File(original,"policy.properties"),new File(own,"policy.properties"));
          copyIfMissing(new File(original,"runtime.properties"),new File(own,"runtime.properties"));
          try(CobraJavaPersistence.Output output=new CobraJavaPersistence.Output(marker)){output.write(new byte[]{'1','\n'});}
        }
      } catch(IOException error) {
        throw new IllegalStateException("Existing refresh settings preserved; Cobra snapshot not durably committed",error);
      }
      return own;
    }
  }
  private static void copyIfMissing(File original,File target)throws IOException {
    if(target.exists()||!original.isFile())return;
    // AtomicFile preserves a complete prior target if publication fails.
    CobraJavaPersistence.Atomic atomic=new CobraJavaPersistence.Atomic(target);
    FileOutputStream output=atomic.startWrite();
    try(FileInputStream input=new FileInputStream(original)) {
      byte[] buffer=new byte[16384];int count;
      while((count=input.read(buffer))!=-1)output.write(buffer,0,count);
      atomic.finishWrite(output);
    } catch(IOException|RuntimeException error) {
      atomic.failWrite(output);throw error;
    }
  }
}
