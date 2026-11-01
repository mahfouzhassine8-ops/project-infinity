package com.projectinfinity.kodi;

import android.app.Activity;
import android.view.View;
import android.widget.LinearLayout;
import java.lang.reflect.Method;

/** Fullscreen presentation only; original Cobra audio owner performs every change. */
public final class CobraFullscreenAudio {
  private CobraFullscreenAudio() {}
  private static final String TAG="cobra_fullscreen_audio";
  private static Object field(Activity a,String name){return CobraArrange.ownedField(a,name);}
  private static Object call(Activity a,String name,Class<?>[] types,Object...args){return CobraArrange.ownedCall(a,name,types,args);}
  private static Object target(Activity a) {
    // A fullscreen Multi-View tile need not be the selected audio tile.
    if(Boolean.TRUE.equals(field(a,"mCobraMultiFullscreenActive"))) {
      Object[] players=(Object[])field(a,"mMultiPlayers");
      int index=(Integer)field(a,"mAudioTile");
      return players!=null && index>=0 && index<players.length?players[index]:null;
    }
    return field(a,"mPlayer");
  }
  private static Class<?> playerClass() {
    try{return Class.forName("androidx.media3.exoplayer.ExoPlayer");}
    catch(ClassNotFoundException e){throw new IllegalStateException("Cobra audio binding",e);}
  }
  private static Object playerCall(Activity a,String name,Object player) {
    return call(a,name,new Class<?>[]{playerClass()},player);
  }
  private static boolean muted(Activity a,Object player) {
    if(Boolean.TRUE.equals(playerCall(a,"cobraMediaMuted",player)))return true;
    try{return ((Float)playerClass().getMethod("getVolume").invoke(player))<=0f;}
    catch(ReflectiveOperationException e){throw new IllegalStateException("Cobra player volume binding",e);}
  }
  private static void text(View v,String name,String value) {
    try {
      Method m=v.getClass().getDeclaredMethod(name,String.class);m.setAccessible(true);m.invoke(v,value);
    } catch(ReflectiveOperationException e){throw new IllegalStateException("Cobra button binding: "+name,e);}
  }
  public static void insert(final Activity a,LinearLayout tools) {
    if(tools.findViewWithTag(TAG)!=null)return;
    View button=(View)call(a,"cobraIcon",new Class<?>[]{String.class,String.class,boolean.class,View.OnClickListener.class},
        "audio","Mute",true,(View.OnClickListener)v->{
          if(Boolean.TRUE.equals(field(a,"mCobraPlayerLocked")))return;
          Object player=target(a);
          if(player!=null)playerCall(a,muted(a,player)?"cobraUserUnmute":"cobraToggleMediaMute",player);
          refresh(a);
        });
    button.setTag(TAG);
    int height=Math.round(52*a.getResources().getDisplayMetrics().density);
    tools.addView(button,1,new LinearLayout.LayoutParams(0,height,1f));
    update(a,button);
  }
  public static void refresh(Activity a) {
    View chrome=(View)field(a,"mPlayerChrome");
    View button=chrome==null?null:chrome.findViewWithTag(TAG);
    if(button!=null)update(a,button);
  }
  private static void update(Activity a,View button) {
    Object player=target(a);
    boolean muted=player!=null && muted(a,player);
    String action=muted?"Unmute":"Mute";
    text(button,"icon",muted?"mute":"audio");text(button,"caption",action);
    button.setContentDescription(action);button.setEnabled(player!=null);
  }
}
