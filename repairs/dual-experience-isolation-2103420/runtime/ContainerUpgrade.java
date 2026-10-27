package com.projectinfinity.kodi;
import android.content.Context;

/** Stable container upgrade hook. The owner performs its own one-time
 * snapshot; Infinity never imports or writes Cobra preference state.
 */
public final class ContainerUpgrade {
  private ContainerUpgrade() {}
  public static void beforeOwnerEntry(Context context){CobraBackgroundSettings.initialize(context);}
}
