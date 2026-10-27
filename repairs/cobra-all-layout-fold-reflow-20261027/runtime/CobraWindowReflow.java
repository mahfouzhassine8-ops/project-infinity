package com.projectinfinity.kodi;

import android.app.Activity;
import android.os.Build;
import android.view.View;
import android.view.ViewTreeObserver;
import android.view.WindowInsets;

/** One observer per Cobra window. Runs after measurement, before rendering.
 * It owns no player, channel, audio, position or persistent state.
 */
public final class CobraWindowReflow implements ViewTreeObserver.OnPreDrawListener, View.OnAttachStateChangeListener {
  public interface Owner {
    View cobraReflowSurface();
    void cobraReflowMeasuredWindow();
  }
  private final Activity activity;
  private final View decor;
  private final Owner owner;
  private ViewTreeObserver observer;
  private View previousSurface;
  private int[] previous;
  private boolean applying;

  private CobraWindowReflow(Activity activity, Owner owner) {
    this.activity=activity;this.owner=owner;decor=activity.getWindow().getDecorView();
    decor.addOnAttachStateChangeListener(this);observe();
  }
  public static void install(Activity activity) {
    if(!(activity instanceof Owner))throw new IllegalArgumentException("Cobra reflow owner required");
    new CobraWindowReflow(activity,(Owner)activity);
  }
  private void observe() {
    ViewTreeObserver next=decor.getViewTreeObserver();
    if(observer==next)return;
    if(observer!=null&&observer.isAlive())observer.removeOnPreDrawListener(this);
    observer=next;
    if(observer.isAlive()){
      // Android transfers floating observers on attachment. Remove a
      // transferred registration before registering on the attached tree.
      observer.removeOnPreDrawListener(this);observer.addOnPreDrawListener(this);
    }
  }
  @Override public void onViewAttachedToWindow(View view){previous=null;observe();}
  @Override public void onViewDetachedFromWindow(View view){
    if(observer!=null&&observer.isAlive())observer.removeOnPreDrawListener(this);
    observer=null;previous=null;previousSurface=null;
  }
  @Override public boolean onPreDraw() {
    if(applying||activity.isFinishing()||activity.isDestroyed())return true;
    View surface=owner.cobraReflowSurface();
    if(surface==null||surface.getWidth()<=0||surface.getHeight()<=0)return true;
    int display=decor.getDisplay()==null?-1:decor.getDisplay().getDisplayId();
    int rotation=decor.getDisplay()==null?-1:decor.getDisplay().getRotation();
    int insets=0;
    if(Build.VERSION.SDK_INT>=23){WindowInsets value=decor.getRootWindowInsets();insets=value==null?0:value.hashCode();}
    int[] current={decor.getWidth(),decor.getHeight(),surface.getWidth(),surface.getHeight(),
      surface.getPaddingLeft(),surface.getPaddingTop(),surface.getPaddingRight(),surface.getPaddingBottom(),
      display,rotation,insets,activity.getResources().getConfiguration().densityDpi,
      Float.floatToIntBits(activity.getResources().getConfiguration().fontScale)};
    if(surface==previousSurface&&java.util.Arrays.equals(previous,current))return true;
    previousSurface=surface;previous=current;applying=true;
    try {owner.cobraReflowMeasuredWindow();} finally {applying=false;}
    // A changed layout needs one further traversal. Never render the old
    // cover-sized rectangles stretched across a newly expanded window.
    decor.requestLayout();decor.invalidate();return false;
  }
}
