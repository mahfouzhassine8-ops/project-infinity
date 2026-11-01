package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.view.Surface;

/** One Cobra-owned policy. No sensor listener or system auto-rotate writes. */
public final class CobraRotationPolicy {
  private CobraRotationPolicy() {}
  private static SharedPreferences prefs(Activity a) {
    return CobraJavaPersistence.preferences(a,"cobra_player_rotation",0);
  }
  public static void toggle(Activity a) {
    SharedPreferences p=prefs(a);
    boolean auto=p.getInt("mode",0)==1;
    SharedPreferences.Editor e=p.edit().putBoolean("universal_policy",true).putInt("mode",auto?0:1);
    if(auto)e.putInt("locked_orientation",displayedOrientation(
        a.getResources().getConfiguration().orientation,
        a.getWindowManager().getDefaultDisplay().getRotation()));
    e.apply();
  }
  static int displayedOrientation(int configuration,int rotation) {
    boolean landscape=configuration==Configuration.ORIENTATION_LANDSCAPE;
    boolean naturalLandscape=((rotation==Surface.ROTATION_0 || rotation==Surface.ROTATION_180)==landscape);
    int[] orientations=naturalLandscape?new int[]{0,9,8,1}:new int[]{1,0,9,8};
    return orientations[rotation & 3];
  }
  public static String description(Activity a) {
    if(prefs(a).getInt("mode",0)==1)return "Auto-rotation on";
    return prefs(a).getBoolean("universal_policy",false)?"Rotation locked to current orientation":"Rotation inactive; enable auto-rotation";
  }
  /** Returns false until the user has opted into the new two-state policy. */
  public static boolean apply(Activity a,boolean constrained) {
    SharedPreferences p=prefs(a);
    if(!p.getBoolean("universal_policy",false))return false;
    int wanted=constrained?ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED:
        p.getInt("mode",0)==1?ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR:
        p.getInt("locked_orientation",ActivityInfo.SCREEN_ORIENTATION_LOCKED);
    if(!a.isFinishing() && !a.isDestroyed() && a.getRequestedOrientation()!=wanted)
      a.setRequestedOrientation(wanted);
    return true;
  }
}
