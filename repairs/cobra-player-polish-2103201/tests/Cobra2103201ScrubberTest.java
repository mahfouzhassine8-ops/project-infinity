package com.projectinfinity.kodi;

import android.app.Application;
import android.content.SharedPreferences;
import android.os.Looper;
import android.os.SystemClock;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.io.File;
import java.lang.reflect.*;
import java.net.ServerSocket;
import java.time.Duration;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Production Activity/Android MotionEvent dispatch. Controlled player metadata;
 * no provider connection, native decoder or physical-device verification. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103201ScrubberTest {
  CobraNavigationUiTest ui;InfinityLiveActivity a;Controlled state;ExoPlayer player;
  FrameLayout overlay;SharedPreferences prefs;ServerSocket server;long down;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  static Object call(Object o,String n,Object...v)throws Exception{return CobraNavigationUiTest.call(o,n,v);}
  static final class Controlled implements InvocationHandler {
    long duration=120000L,position=60000L;boolean requested=true,seekable=true;
    int prepares,mediaChanges;final List<Long> seeks=new ArrayList<>();
    final TrackSelectionParameters tracks=new TrackSelectionParameters.Builder(RuntimeEnvironment.getApplication()).build();
    public Object invoke(Object proxy,Method m,Object[] args){String n=m.getName();
      if(n.equals("equals"))return proxy==args[0];if(n.equals("hashCode"))return System.identityHashCode(proxy);
      if(n.equals("toString"))return "Controlled timeline player";
      if(n.equals("getDuration"))return duration;if(n.equals("getCurrentPosition")||n.equals("getContentPosition"))return position;
      if(n.equals("isCurrentMediaItemSeekable"))return seekable;
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return requested;
      if(n.equals("play")){requested=true;return null;}if(n.equals("pause")){requested=false;return null;}
      if(n.equals("setPlayWhenReady")){requested=(Boolean)args[0];return null;}
      if(n.equals("setMediaItem")){mediaChanges++;duration=C.TIME_UNSET;seekable=false;return null;}
      if(n.equals("prepare")){prepares++;return null;}
      if(n.equals("seekTo")){position=((Number)args[args.length-1]).longValue();seeks.add(position);return null;}
      if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getVideoSize"))return VideoSize.UNKNOWN;if(n.equals("getCurrentTracks"))return Tracks.EMPTY;
      if(n.equals("getTrackSelectionParameters"))return tracks;
      if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      if(n.equals("getAvailableCommands"))return Player.Commands.EMPTY;
      if(n.equals("getCurrentCues"))return androidx.media3.common.text.CueGroup.EMPTY_TIME_ZERO;
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==long.class)return 0L;if(t==int.class)return 0;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @Before public void before()throws Exception{
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(8);prefs=(SharedPreferences)get(a,"mPrefs");
    prefs.edit().putBoolean("cobra_live_rewind_enabled",true).commit();
    state=new Controlled();player=proxy(state);put(a,"mPlayer",player);put(a,"mPlaying",((List<?>)get(a,"mChannels")).get(0));
    put(a,"mCobraTimeshiftPlayer",player);call(a,"openPlayerOverlay",get(a,"mPlaying"));ui.measure(a,412,915);
    overlay=(FrameLayout)get(a,"mPlayerOverlay");settle();
  }
  ExoPlayer proxy(Controlled c){return (ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},c);}
  @After public void after()throws Exception{if(server!=null)server.close();if(a!=null){put(a,"mCobraTimeshiftSession",null);ui.clean(a);}CobraVisualRenderer.clients.clear();}
  void settle()throws Exception{ui.measure(a,412,915);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(200));}
  SeekBar seek()throws Exception{return (SeekBar)get(a,"mCobraTimeshiftSeek");}
  View timeline(){return overlay.findViewWithTag("cobra_unified_live_timeline");}
  float[] point(View view,float fraction){android.graphics.Rect r=new android.graphics.Rect();view.getDrawingRect(r);overlay.offsetDescendantRectToMyCoords(view,r);return new float[]{r.left+r.width()*fraction,r.exactCenterY()};}
  void event(int action,float[] p){if(action==MotionEvent.ACTION_DOWN)down=SystemClock.uptimeMillis();MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,p[0],p[1],0);try{assertTrue(overlay.dispatchTouchEvent(e));}finally{e.recycle();}}
  void hold(){Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(ViewConfiguration.getLongPressTimeout()+80));}
  void noDrawer()throws Exception{assertNull("Timeline hold must not open Channels",get(a,"mCobraPlayerDrawer"));}
  @SuppressWarnings("unchecked") Object local(boolean ready)throws Exception{
    Object session=CobraNavigationUiTest.construct("CobraLocalTimeshiftSession",a.getCacheDir(),"https://example.invalid/live.ts",Collections.emptyMap(),120,0);
    server=new ServerSocket(0);put(session,"server",server);put(session,"ready",ready);
    Class<?> type=Class.forName(InfinityLiveActivity.class.getName()+"$CobraLocalTimeshiftSession$Segment");Constructor<?> ctor=type.getDeclaredConstructors()[0];ctor.setAccessible(true);
    ((Deque<Object>)get(session,"segments")).add(ctor.newInstance(1L,120000L,0L,18800L,new File(a.getCacheDir(),"fixture-only.ts"),false,0L));
    put(a,"mCobraTimeshiftSession",session);put(a,"mCobraTimeshiftPlayer",null);put(a,"mCobraTimeshiftProxyPlayer",player);
    state.seekable=false;state.duration=C.TIME_UNSET;call(a,"cobraUpdateTimeshiftSeek");settle();return session;
  }
  @Test public void warmingTimelineHoldCannotOpenChannelDrawer()throws Exception{
    local(false);assertEquals(View.GONE,seek().getVisibility());float[] p=point(timeline(),.5f);event(MotionEvent.ACTION_DOWN,p);hold();noDrawer();event(MotionEvent.ACTION_UP,p);assertEquals(0,state.mediaChanges);
  }
  @Test public void rewindOffTimelineOwnsItsTouchWithoutEnablingSeeking()throws Exception{
    prefs.edit().putBoolean("cobra_live_rewind_enabled",false).commit();call(a,"cobraUpdateTimeshiftSeek");settle();assertEquals(View.GONE,seek().getVisibility());
    float[] p=point(timeline(),.5f);event(MotionEvent.ACTION_DOWN,p);hold();noDrawer();event(MotionEvent.ACTION_UP,p);assertTrue(state.seeks.isEmpty());
  }
  @Test public void readyLocalHistoryExposesThumbBeforeTransportActivation()throws Exception{
    local(true);assertEquals(View.VISIBLE,seek().getVisibility());assertEquals(1000,seek().getProgress());assertEquals(0,state.mediaChanges);assertEquals(0,state.prepares);
  }
  @Test public void readyDragCommitsOnceOnReleaseAndPreservesPause()throws Exception{
    local(true);state.requested=false;float[] start=point(timeline(),.75f),end=point(timeline(),.25f);
    event(MotionEvent.ACTION_DOWN,start);hold();noDrawer();event(MotionEvent.ACTION_MOVE,end);int chosen=seek().getProgress();
    assertEquals(0,state.mediaChanges);assertEquals(0,state.prepares);assertTrue(state.seeks.isEmpty());
    event(MotionEvent.ACTION_UP,end);assertEquals(1,state.mediaChanges);assertEquals(1,state.prepares);assertFalse(state.requested);assertSame(player,get(a,"mCobraTimeshiftPlayer"));
    state.duration=120000L;state.seekable=true;
    Object binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,player,get(a,"mPlaying"));
    ((Map)get(a,"mCobraPlayerBindings")).put(player,binding);
    call(binding,"onPlaybackStateChanged",Player.STATE_READY);
    assertEquals(Collections.singletonList(120000L*chosen/1000L),state.seeks);assertFalse(state.requested);
    call(binding,"onPlaybackStateChanged",Player.STATE_READY);assertEquals(1,state.seeks.size());
  }
  @Test public void cancelledReadyDragNeverChangesTransport()throws Exception{
    local(true);float[] p=point(timeline(),.3f);event(MotionEvent.ACTION_DOWN,p);hold();event(MotionEvent.ACTION_CANCEL,p);
    noDrawer();assertEquals(0,state.mediaChanges);assertTrue(state.seeks.isEmpty());assertEquals(Boolean.FALSE,get(a,"mCobraTimeshiftDragging"));
  }
  @Test public void activeScrubMovesPreviewButSeeksOnlyOnRelease()throws Exception{
    float[] p=point(timeline(),.25f);event(MotionEvent.ACTION_DOWN,p);hold();noDrawer();
    for(float f:new float[]{.35f,.55f,.75f})event(MotionEvent.ACTION_MOVE,point(timeline(),f));
    assertTrue("Dragging must not cause repeated decoder seeks",state.seeks.isEmpty());int chosen=seek().getProgress();event(MotionEvent.ACTION_UP,point(timeline(),.75f));
    assertEquals(Collections.singletonList(120000L*chosen/1000L),state.seeks);assertEquals(0,state.prepares);
  }
  @Test public void nativeSeekableLiveWindowUsesExistingTimeline()throws Exception{
    put(a,"mCobraTimeshiftPlayer",null);call(a,"cobraUpdateTimeshiftSeek");assertEquals(View.VISIBLE,seek().getVisibility());assertEquals(500,seek().getProgress());
  }
  @Test public void channelChangeCancelsOldGesture()throws Exception{
    float[] p=point(timeline(),.25f);event(MotionEvent.ACTION_DOWN,p);Controlled next=new Controlled();put(a,"mPlayer",proxy(next));
    event(MotionEvent.ACTION_UP,p);assertTrue(state.seeks.isEmpty());assertTrue(next.seeks.isEmpty());
  }
  @Test public void detachedSeekbarCannotCommitOrClearNewGesture()throws Exception{
    SeekBar old=seek();float[] p=point(timeline(),.25f);event(MotionEvent.ACTION_DOWN,p);call(a,"cobraBuildPlayerChrome");settle();
    put(a,"mCobraTimeshiftDragging",true);MotionEvent end=MotionEvent.obtain(down,SystemClock.uptimeMillis(),MotionEvent.ACTION_UP,old.getWidth()*.25f,old.getHeight()*.5f,0);
    try{old.dispatchTouchEvent(end);}finally{end.recycle();}assertTrue(state.seeks.isEmpty());assertEquals(Boolean.TRUE,get(a,"mCobraTimeshiftDragging"));
  }
  @Test public void actualVideoBackgroundHoldStillOpensChannels()throws Exception{
    float[] p={overlay.getWidth()*.5f,overlay.getHeight()*.3f};event(MotionEvent.ACTION_DOWN,p);hold();assertNotNull(get(a,"mCobraPlayerDrawer"));event(MotionEvent.ACTION_CANCEL,p);
  }
  @Test public void cancelledActiveDragDoesNotSeek()throws Exception{
    float[] p=point(timeline(),.2f);event(MotionEvent.ACTION_DOWN,p);event(MotionEvent.ACTION_MOVE,point(timeline(),.8f));event(MotionEvent.ACTION_CANCEL,p);
    assertTrue(state.seeks.isEmpty());assertEquals(500,seek().getProgress());
  }
  @Test public void pendingFirstSeekCannotAffectReplacementSession()throws Exception{
    local(true);call(a,"cobraCommitTimelineSeek",250);state.duration=120000L;state.seekable=true;put(a,"mCobraTimeshiftSession",null);
    call(a,"cobraApplyPendingTimelineSeek",player);assertTrue(state.seeks.isEmpty());assertEquals(-1,get(a,"mCobraPendingTimelineValue"));
  }
  @Test public void dpadSeekUsesTheSameTimelineOwner()throws Exception{
    seek().requestFocus();int before=seek().getProgress();assertTrue(seek().onKeyDown(KeyEvent.KEYCODE_DPAD_LEFT,new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_LEFT)));
    assertTrue(seek().getProgress()<before);assertEquals(Collections.singletonList(120000L*seek().getProgress()/1000L),state.seeks);
  }
  @Test public void continuedDpadSeekingKeepsControlsVisible()throws Exception{
    call(a,"showPlayerChromeTemporarily");seek().requestFocus();
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(3000));
    assertTrue(seek().onKeyDown(KeyEvent.KEYCODE_DPAD_LEFT,new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_LEFT)));
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(700));
    assertEquals(View.VISIBLE,((View)get(a,"mPlayerChrome")).getVisibility());
    assertEquals(1f,((View)get(a,"mPlayerChrome")).getAlpha(),.01f);
  }
}
