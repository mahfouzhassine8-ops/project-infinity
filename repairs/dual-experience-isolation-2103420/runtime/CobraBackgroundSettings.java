package com.projectinfinity.kodi;

import android.content.Context;
import android.content.SharedPreferences;
import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.channels.FileLock;

/** One-time lossless snapshot of the previously shared boolean. No old data is
 * deleted or rewritten. The marker is published only after protected commit,
 * readback, file sync and directory sync have all succeeded.
 */
public final class CobraBackgroundSettings {
  private static final Object LOCK=new Object();
  public static final String STORE="cobra_background_runtime";
  public static final String ROTATION_STORE="cobra_player_rotation";
  private CobraBackgroundSettings() {}
  public static void initialize(Context context) {
    synchronized(LOCK) {
      File marker=new File(context.getFilesDir(),"cobra-settings-isolation-v1.ready");
      if(marker.isFile())return;
      File guard=new File(context.getFilesDir(),"cobra-settings-isolation-v1.lock");
      try(RandomAccessFile file=new RandomAccessFile(guard,"rw"); FileLock held=file.getChannel().lock()) {
        if(marker.isFile())return;
        SharedPreferences own=CobraJavaPersistence.preferences(context,STORE,0);
        boolean value=own.contains("extended_background")?own.getBoolean("extended_background",false):
            context.getSharedPreferences("infinity_runtime",0).getBoolean("extended_background",false);
        if(!own.edit().putBoolean("extended_background",value).commit())
          throw new IOException("Cobra background preference snapshot was not durably saved");
        SharedPreferences rotation=CobraJavaPersistence.preferences(context,ROTATION_STORE,0);
        SharedPreferences oldRotation=context.getSharedPreferences("infinity_player_rotation",0);
        if(!rotation.contains("mode")&&oldRotation.contains("mode")&&
           !rotation.edit().putInt("mode",oldRotation.getInt("mode",0)).commit())
          throw new IOException("Cobra rotation preference snapshot was not durably saved");
        try(CobraJavaPersistence.Output output=new CobraJavaPersistence.Output(marker)) {
          output.write(new byte[]{'1','\n'});
        }
      } catch(IOException error) {
        throw new IllegalStateException("Existing background settings preserved; isolation seed not committed",error);
      }
    }
  }
  public static SharedPreferences preferences(Context context) {
    initialize(context);
    return CobraJavaPersistence.preferences(context,STORE,0);
  }
}
