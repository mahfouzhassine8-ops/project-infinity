package com.projectinfinity.kodi;
import android.content.Context;
import android.content.SharedPreferences;

/** Chooser-facing access to Cobra's existing appearance preferences.
 * There is exactly one protected wrapper/cache/queue owner for this store.
 */
public final class CobraPreferencePort {
  private CobraPreferencePort() {}
  public static SharedPreferences preferences(Context context,String name,int mode) {
    if(!"infinity_cobra_live".equals(name)||mode!=0)throw new IllegalArgumentException("Cobra appearance store required");
    CobraJavaPersistence.userEntry(context);
    return CobraJavaPersistence.preferences(context,name,mode);
  }
}
