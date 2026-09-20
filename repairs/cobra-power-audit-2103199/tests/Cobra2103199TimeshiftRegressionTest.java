package com.projectinfinity.kodi;

import android.app.Application;
import android.os.Looper;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.SeekBar;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.net.ServerSocket;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Cobra callbacks with Android controls and a deterministic player boundary.
 * Does not claim codec, stream, physical Fold, PiP or rendered video verification.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103199TimeshiftRegressionTest {
  CobraNavigationUiTest ui;
  InfinityLiveActivity activity;
  StubPlayer state;
  ExoPlayer player;

  static Object get(Object owner,String name)throws Exception {
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(owner);
  }
  static void set(Object owner,String name,Object value)throws Exception {
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);
  }
  static Object call(Object owner,String name,Object...args)throws Exception {
    for(Method m:owner.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){
      m.setAccessible(true);try{return m.invoke(owner,args);}catch(InvocationTargetException e){throw new AssertionError(name,e.getCause());}
    }
    throw new NoSuchMethodException(name);
  }
  static final class StubPlayer implements InvocationHandler {
    long duration=120000L,position=30000L;
    boolean requested=true,seekable=true;
    int prepares=0,mediaChanges=0;
    @Override public Object invoke(Object proxy,Method method,Object[] args){
      String n=method.getName();
      if(n.equals("equals"))return proxy==args[0];
      if(n.equals("hashCode"))return System.identityHashCode(proxy);
      if(n.equals("toString"))return "DeterministicTimeshiftPlayer";
      if(n.equals("getDuration"))return duration;
      if(n.equals("getCurrentPosition")||n.equals("getContentPosition"))return position;
      if(n.equals("isCurrentMediaItemSeekable"))return seekable;
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return requested;
      if(n.equals("play")){requested=true;return null;}
      if(n.equals("pause")){requested=false;return null;}
      if(n.equals("setPlayWhenReady")){requested=(Boolean)args[0];return null;}
      if(n.equals("prepare")){prepares++;return null;}
      if(n.equals("setMediaItem")){mediaChanges++;return null;}
      if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getVideoSize"))return VideoSize.UNKNOWN;
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;
      if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;
      if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;
      if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      if(n.equals("getAvailableCommands"))return Player.Commands.EMPTY;
      if(n.equals("getCurrentCues"))return androidx.media3.common.text.CueGroup.EMPTY_TIME_ZERO;
      Class<?> type=method.getReturnType();
      if(type==boolean.class)return false;if(type==long.class)return 0L;if(type==int.class)return 0;if(type==float.class)return 0f;if(type==double.class)return 0d;
      return null;
    }
  }

  @Before public void before()throws Exception {
    ui=new CobraNavigationUiTest();ui.clock();activity=ui.fixture(24);
    state=new StubPlayer();player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},state);
    set(activity,"mPlayer",player);set(activity,"mCobraTimeshiftPlayer",player);
    Object channel=((List<?>)get(activity,"mChannels")).get(0);set(activity,"mPlaying",channel);
    ((android.content.SharedPreferences)get(activity,"mPrefs")).edit().putBoolean("cobra_live_rewind_enabled",true).commit();
    SeekBar seek=new SeekBar(activity);seek.setMax(1000);set(activity,"mCobraTimeshiftSeek",seek);
    ProgressBar progress=new ProgressBar(activity,null,android.R.attr.progressBarStyleHorizontal);progress.setMax(1000);set(activity,"mCobraPlayerProgramProgress",progress);
    set(activity,"mCobraLiveRewindButton",call(activity,"cobraIcon","prev","Rewind Live TV 30 seconds",true,null));
    set(activity,"mCobraGoLiveButton",call(activity,"cobraIcon","play","Go Live",true,null));
    set(activity,"mCobraLastTickerMinute",(int)(System.currentTimeMillis()/60000L));
  }
  @After public void after()throws Exception {if(activity!=null)ui.clean(activity);}
  SeekBar seek()throws Exception{return (SeekBar)get(activity,"mCobraTimeshiftSeek");}
  ProgressBar progress()throws Exception{return (ProgressBar)get(activity,"mCobraPlayerProgramProgress");}
  void tick()throws Exception{((Runnable)get(activity,"mCobraPresentationTick")).run();}

  @Test public void ordinaryClockProgressMovesExistingTimelineWithoutPlayerEvents()throws Exception {
    call(activity,"cobraUpdateTimeshiftSeek");assertEquals(250,seek().getProgress());
    state.position=60000L;tick();assertEquals(500,seek().getProgress());assertEquals(500,progress().getProgress());
  }
  @Test public void rewindRecoversFromOldestBoundaryAsPlaybackAdvances()throws Exception {
    state.position=0L;call(activity,"cobraUpdateLiveRewindControls");assertFalse(((View)get(activity,"mCobraLiveRewindButton")).isEnabled());
    state.position=2000L;tick();assertTrue(((View)get(activity,"mCobraLiveRewindButton")).isEnabled());
  }
  @Test public void activeDragOwnsBothThumbAndSharedBlueLine()throws Exception {
    set(activity,"mCobraTimeshiftDragging",true);seek().setProgress(750);progress().setProgress(750);
    tick();assertEquals(750,seek().getProgress());assertEquals(750,progress().getProgress());
    set(activity,"mCobraTimeshiftDragging",false);tick();assertEquals(250,seek().getProgress());assertEquals(250,progress().getProgress());
  }
  @Test public void unavailableDurationDoesNotPresentAFalseSeekWindow()throws Exception {
    state.duration=C.TIME_UNSET;tick();assertEquals(View.GONE,seek().getVisibility());
    state.duration=120000L;state.seekable=false;tick();assertEquals(View.GONE,seek().getVisibility());
  }
  @Test public void pausedClockRefreshDoesNotResumeThePlayer()throws Exception {
    state.requested=false;state.position=45000L;tick();assertFalse(state.requested);assertEquals(375,seek().getProgress());
  }
  @Test public void switchingPausedProxyIntoExistingHlsWindowPreservesPause()throws Exception {
    Class<?> sessionClass=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$CobraLocalTimeshiftSession");
    Constructor<?> constructor=sessionClass.getDeclaredConstructor(java.io.File.class,String.class,Map.class,int.class,int.class);constructor.setAccessible(true);
    Object session=constructor.newInstance(activity.getCacheDir(),"https://example.invalid/live.ts",Collections.emptyMap(),120,0);
    try(ServerSocket server=new ServerSocket(0)) {
      set(session,"server",server);set(session,"ready",true);
      set(activity,"mCobraTimeshiftSession",session);set(activity,"mCobraTimeshiftProxyPlayer",player);set(activity,"mCobraTimeshiftPlayer",null);
      state.requested=false;
      assertEquals(Boolean.TRUE,call(activity,"cobraActivateLocalTimeshift",player,get(activity,"mPlaying"),30000L));
      assertFalse(state.requested);assertEquals(1,state.prepares);assertEquals(1,state.mediaChanges);
      assertSame(player,get(activity,"mCobraTimeshiftPlayer"));assertNull(get(activity,"mCobraTimeshiftProxyPlayer"));
    } finally {set(activity,"mCobraTimeshiftSession",null);}
  }
  @Test public void rebuiltChromeDoesNotInheritDetachedSeekbarsGesture()throws Exception {
    android.widget.FrameLayout overlay=new android.widget.FrameLayout(activity);
    activity.setContentView(overlay);
    overlay.measure(View.MeasureSpec.makeMeasureSpec(412,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(915,View.MeasureSpec.EXACTLY));
    overlay.layout(0,0,412,915);set(activity,"mPlayerOverlay",overlay);
    set(activity,"mCobraTimeshiftDragging",true);
    call(activity,"cobraBuildPlayerChrome");
    assertEquals(Boolean.FALSE,get(activity,"mCobraTimeshiftDragging"));
    state.position=60000L;tick();assertEquals(500,seek().getProgress());
  }

}
