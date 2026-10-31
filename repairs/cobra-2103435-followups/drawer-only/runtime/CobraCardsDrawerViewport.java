package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.res.Configuration;
import android.view.View;
import java.lang.ref.WeakReference;
import java.util.WeakHashMap;

/** Coordinates for the active Cards drawer journey, never a cached viewport.
 * Main-thread layout callers own this bounded, weak Activity/drawer state.
 * Neither animator nor layout dimensions are mutated here. */
public final class CobraCardsDrawerViewport {
  private static final WeakHashMap<Activity,Journey> JOURNEYS=new WeakHashMap<>();
  private CobraCardsDrawerViewport(){}
  private static Object read(Activity a,String name){return CobraArrange.ownedField(a,name);}
  private static boolean shown(Object v){return v instanceof View && ((View)v).isAttachedToWindow() && ((View)v).isShown();}
  private static final class Journey {
    final WeakReference<View> stage,drawer;
    boolean inner;
    Journey(View stage,View drawer,boolean inner){this.stage=new WeakReference<>(stage);this.drawer=new WeakReference<>(drawer);this.inner=inner;}
  }

  public static void location(Activity owner,View shell,int[] xy){
    shell.getLocationInWindow(xy);
    if(owner==null || !"cards".equals(read(owner,"mCobraGuideStyle"))
        || Boolean.TRUE.equals(read(owner,"mCobraProActive"))
        || Boolean.TRUE.equals(read(owner,"mCobraProSportsActive")))return;
    if(shell!=read(owner,"mCobraGuideShell") || !shell.isAttachedToWindow() || !shell.isShown())return;
    Object candidate=read(owner,"mStage");
    if(!(candidate instanceof View) || shell.getParent()!=candidate
        || shown(read(owner,"mPlayerOverlay")) || shown(read(owner,"mMultiOverlay")))return;
    View stage=(View)candidate;
    View drawer=owner.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");
    float translation=stage.getTranslationX();
    if(drawer==null && translation==0f){JOURNEYS.remove(owner);return;}
    Configuration config=owner.getResources().getConfiguration();
    boolean inner=Math.min(config.screenWidthDp,config.screenHeightDp)>=600;
    Journey journey=JOURNEYS.get(owner);
    // A new actual drawer (or shell stage) starts a new journey. A normal
    // front-display drawer can never inherit a previous inner-display guard.
    if(journey==null || journey.stage.get()!=stage || drawer!=null && journey.drawer.get()!=drawer){
      journey=new Journey(stage,drawer,inner);JOURNEYS.put(owner,journey);
    }else if(inner)journey.inner=true;
    if(!journey.inner)return;
    // Original435 drawer animation is the sole nonzero writer of stage X.
    // Exclude only that presentation translation. Genuine insets, layout
    // origin, current shell/window size and the original animation survive.
    // Retain ownership through close-tail frames and real inner->cover reflow.
    xy[0]-=Math.round(translation);
  }
}
