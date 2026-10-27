package com.projectinfinity.kodi;
import android.content.Context;
import android.content.SharedPreferences;

/** Stable container setting exposed by the single experience chooser. */
public final class ExperienceLaunchPreferences {
  private ExperienceLaunchPreferences() {}
  public static SharedPreferences preferences(Context context,String name,int mode) {
    if(!"infinity_experience".equals(name)||mode!=0)throw new IllegalArgumentException("Launcher preference store required");
    return ShellJavaPersistence.preferences(context,name,mode);
  }
}
