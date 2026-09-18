package com.projectinfinity.kodi;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.res.Configuration;
import android.media.session.*;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Activity/service/view wiring. Does not claim physical codecs or SystemUI testing. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103164PlaybackStabilityTest {
  CobraNavigationUiTest ui; Application app; InfinityLiveActivity a;
  InfinityExtendedBackgroundService service;
  static Object get(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
  static void set(Object o,String n,Object v)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
  static Object call(Object o,String n,Object...args)throws Exception{
    Class<?> c=o instanceof Class?(Class<?>)o:o.getClass();
    for(Method m:c.getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterCount()==args.length){m.setAccessible(true);return m.invoke(o instanceof Class?null:o,args);}
    throw new NoSuchMethodException(n);
  }
  @Before public void before()throws Exception{
    app=RuntimeEnvironment.getApplication();Shadows.shadowOf(app).grantPermissions(Manifest.permission.POST_NOTIFICATIONS);
    app.getSharedPreferences("infinity_runtime",0).edit().clear().commit();
    InfinityExtendedBackgroundService.stopMiniPlayback(app);
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);
    policy().resume(false);
  }
  @After public void after()throws Exception{
    InfinityExtendedBackgroundService.stopMiniPlayback(app);
    if(service!=null)service.onDestroy();
    if(a!=null)ui.clean(a);
    CobraVisualRenderer.clients.clear();
  }
  InfinityLiveActivity.CobraPlaybackPolicy policy()throws Exception{return (InfinityLiveActivity.CobraPlaybackPolicy)get(a,"mCobraPlaybackPolicy");}
  final class Controlled {
    int state=Player.STATE_READY,plays=0,pauses=0,prepares=0;boolean requested=true;
    final ArrayList<Player.Listener> listeners=new ArrayList<>();
    final ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(getClass().getClassLoader(),new Class[]{ExoPlayer.class},(p,m,args)->{
      String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(p);if(n.equals("equals"))return p==args[0];if(n.equals("toString"))return "ControlledCobra";
      if(n.equals("addListener")){listeners.add((Player.Listener)args[0]);return null;}
      if(n.equals("removeListener")){listeners.remove(args[0]);return null;}
      if(n.equals("pause")||n.equals("play")){boolean value=n.equals("play");if(value)plays++;else pauses++;boolean changed=requested!=value;requested=value;
        if(changed)for(Player.Listener l:new ArrayList<>(listeners))l.onPlayWhenReadyChanged(value,Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST);return null;}
      if(n.equals("prepare")){prepares++;return null;}
      if(n.equals("getPlaybackState"))return state;if(n.equals("getPlayWhenReady"))return requested;
      if(n.equals("isPlaying"))return requested&&state==Player.STATE_READY;
      if(n.equals("getCurrentPosition"))return 17000L;
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);
      if(n.equals("getVideoFormat"))return new Format.Builder().setSampleMimeType("video/avc").build();
      if(n.equals("getTrackSelectionParameters"))return new TrackSelectionParameters.Builder(app).build();
      if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    });
  }
  Controlled fullscreen()throws Exception{
    Controlled c=new Controlled();FrameLayout root=new FrameLayout(a);a.setContentView(root);set(a,"mPlayerOverlay",root);set(a,"mPlayer",c.player);return c;
  }
  Controlled mini()throws Exception{
    Controlled c=new Controlled();set(a,"mPlayer",null);set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);set(a,"mCobraPreviewPlayer",c.player);
    ((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_mini_background_playback",true).commit();return c;
  }
  @SuppressWarnings("unchecked") void bind(Controlled c)throws Exception{
    for(Class<?> nested:InfinityLiveActivity.class.getDeclaredClasses())if(nested.getSimpleName().equals("CobraPlayerBinding")){
      Constructor<?> ctor=nested.getDeclaredConstructors()[0];ctor.setAccessible(true);Object binding=ctor.newInstance(a,c.player,null);
      ((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(c.player,binding);c.listeners.add((Player.Listener)binding);return;
    }throw new AssertionError("binding missing");
  }
  @Test public void closingPipWhileCachedFlagIsTrueStopsAudio()throws Exception{
    Controlled c=fullscreen();policy().pause();policy().pipChanged(true);set(a,"mInPictureInPicture",true);
    call(a,"onStop");assertFalse(c.requested);assertTrue(policy().dismissed);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
    assertTrue(((Map<?,?>)get(a,"mBackgroundResumePlayers")).isEmpty());
  }
  @Test public void pipFalseBeforeOnStopCannotBecomeMiniAudio()throws Exception{
    Controlled c=fullscreen();policy().pause();policy().pipChanged(true);
    call(a,"onPictureInPictureModeChanged",false,new Configuration());call(a,"onStop");assertFalse(c.requested);assertTrue(policy().dismissed);
  }
  @Test public void pipFalseAfterOnStopCannotRestartPlayback()throws Exception{
    Controlled c=fullscreen();policy().pause();policy().pipChanged(true);set(a,"mInPictureInPicture",true);
    call(a,"onStop");call(a,"onPictureInPictureModeChanged",false,new Configuration());call(a,"startCobraPlayer",c.player);
    assertFalse(c.requested);assertEquals(0,c.plays);assertTrue(((Map<?,?>)get(a,"mBackgroundResumePlayers")).isEmpty());
  }
  @Test public void expandingPipAfterResumeClearsOwnershipWithoutPause()throws Exception{
    Controlled c=fullscreen();policy().pause();policy().pipChanged(true);policy().resume(true);
    call(a,"onPictureInPictureModeChanged",false,new Configuration());assertFalse(policy().pipOwned);assertTrue(c.requested);assertEquals(0,c.pauses);
  }
  @Test public void expandingPipBeforeResumePreservesPlayback()throws Exception{
    Controlled c=fullscreen();policy().pause();policy().pipChanged(true);
    call(a,"onPictureInPictureModeChanged",false,new Configuration());policy().resume(false);assertFalse(policy().pipOwned);assertTrue(c.requested);
  }
  @Test public void lifecyclePauseStillResumesExactSamePlayer()throws Exception{
    Controlled c=fullscreen();bind(c);call(a,"pauseCobraForBackground");assertFalse(c.requested);
    assertTrue(((Map<?,?>)get(a,"mBackgroundResumePlayers")).containsKey(c.player));call(a,"resumeCobraAfterBackground");assertTrue(c.requested);assertEquals(0,c.prepares);
  }
  @Test public void bufferingFullscreenRemainsEligibleButUserPauseDoesNot()throws Exception{
    Controlled c=fullscreen();c.state=Player.STATE_BUFFERING;assertEquals(Boolean.TRUE,call(a,"cobraWantsFullscreenPip"));c.requested=false;assertEquals(Boolean.FALSE,call(a,"cobraWantsFullscreenPip"));
  }
  @Test public void miniToggleOffDoesNotPermitHiddenAudio()throws Exception{
    Controlled c=mini();((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_mini_background_playback",false).commit();call(a,"onStop");assertFalse(c.requested);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
  }
  @Test public void permittedMiniKeepsOnlyItsExistingPlayer()throws Exception{
    Controlled c=mini(),other=new Controlled();set(a,"mCobraCarryPlayer",other.player);call(a,"onStop");assertTrue(c.requested);assertFalse(other.requested);
    assertSame(c.player,get(a,"mCobraMiniBackgroundPlayer"));assertEquals(0,c.prepares);assertEquals(0,c.plays);
  }
  @Test public void returningBeforeServiceStartsRevokesPendingGrant()throws Exception{
    Controlled c=mini();assertEquals(Boolean.TRUE,call(a,"cobraBeginMiniBackgroundPlayback"));assertTrue(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
    call(a,"cobraEndMiniBackgroundPlayback");service=Robolectric.buildService(InfinityExtendedBackgroundService.class).create().get();
    service.onStartCommand(new Intent().setAction("com.projectinfinity.kodi.action.MINI_BACKGROUND_START"),0,1);
    assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(service,"mMediaSession"));assertTrue(c.requested);
  }
  @Test public void fullscreenNeverGrantsMiniEvenWithToggleOn()throws Exception{
    mini();Controlled c=fullscreen();assertEquals(Boolean.FALSE,call(a,"cobraBeginMiniBackgroundPlayback"));assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertTrue(c.requested);
  }
  @Test public void notificationPermissionDeniedPausesRatherThanHidingAudio()throws Exception{
    Controlled c=mini();Shadows.shadowOf(app).denyPermissions(Manifest.permission.POST_NOTIFICATIONS);call(a,"onStop");assertFalse(c.requested);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
  }
  static final class Owner implements InfinityExtendedBackgroundService.MiniPlaybackOwner {
    boolean available=true;int playback=PlaybackState.STATE_PLAYING,command=0,unavailable=0;
    public boolean available(){return available;}public int state(){return playback;}public long position(){return 17000L;}
    public void command(int value){command=value;if(value==2)playback=PlaybackState.STATE_PAUSED;if(value==1)playback=PlaybackState.STATE_PLAYING;if(value==3)available=false;}
    public void unavailable(){unavailable++;available=false;}
  }
  Owner media()throws Exception{
    Owner owner=new Owner();assertTrue(InfinityExtendedBackgroundService.startMiniPlayback(app,"Test channel",owner));
    service=Robolectric.buildService(InfinityExtendedBackgroundService.class).create().get();service.onStartCommand(new Intent(),0,1);
    assertNotNull(get(service,"mMediaSession"));return owner;
  }
  // Static fields are read explicitly because reflection on Class itself would target java.lang.Class.
  long grantGeneration()throws Exception{Field f=InfinityExtendedBackgroundService.class.getDeclaredField("sMiniGrant");f.setAccessible(true);return ((InfinityExtendedBackgroundService.MiniGrant)f.get(null)).generation;}
  @Test public void nativeMediaStateUsesRealPositionAndPausedStatus()throws Exception{
    Owner o=media();PlaybackState state=(PlaybackState)call(service,"cobraMiniPlaybackState",o);
    assertEquals(17000L,state.getPosition());assertEquals(PlaybackState.STATE_PLAYING,state.getState());assertEquals(1f,state.getPlaybackSpeed(),0f);
    o.playback=PlaybackState.STATE_PAUSED;InfinityExtendedBackgroundService.refreshMiniPlayback(o);
    state=(PlaybackState)call(service,"cobraMiniPlaybackState",o);assertEquals(PlaybackState.STATE_PAUSED,state.getState());assertEquals(0f,state.getPlaybackSpeed(),0f);
  }
  @Test public void nativeCommandPausesCurrentOwner()throws Exception{
    Owner o=media();call(InfinityExtendedBackgroundService.class,"dispatchMiniCommand",grantGeneration(),2);
    assertEquals(2,o.command);assertEquals(PlaybackState.STATE_PAUSED,o.playback);
    assertEquals(PlaybackState.STATE_PAUSED,((PlaybackState)call(service,"cobraMiniPlaybackState",o)).getState());
  }
  @Test public void nativeMediaSessionCallbackReachesOwner()throws Exception{
    Owner o=media();MediaSession.Callback callback=(MediaSession.Callback)call(service,"cobraMiniMediaCallback",grantGeneration());
    callback.onPause();assertEquals(2,o.command);assertEquals(PlaybackState.STATE_PAUSED,o.playback);
  }
  @Test public void oldNotificationCannotControlReplacementSession()throws Exception{
    Owner old=media();long token=grantGeneration();InfinityExtendedBackgroundService.stopMiniPlayback(app);
    Owner replacement=new Owner();assertTrue(InfinityExtendedBackgroundService.startMiniPlayback(app,"New",replacement));service.onStartCommand(new Intent(),0,2);
    call(InfinityExtendedBackgroundService.class,"dispatchMiniCommand",token,3);assertEquals(0,replacement.command);assertEquals(0,old.command);assertTrue(replacement.available);
  }
  @Test public void staleActivityCannotStopNewMiniOwner()throws Exception{
    Owner old=media(),replacement=new Owner();assertTrue(InfinityExtendedBackgroundService.startMiniPlayback(app,"Replacement",replacement));
    InfinityExtendedBackgroundService.stopMiniPlayback(app,old);assertTrue(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertTrue(replacement.available);assertFalse(old.available);
  }
  @Test public void invalidNativeCommandCannotPausePlayback()throws Exception{
    Owner owner=media();call(InfinityExtendedBackgroundService.class,"dispatchMiniCommand",grantGeneration(),0);assertEquals(0,owner.command);assertTrue(owner.available);
  }
  @Test public void notificationStopRemovesMediaPresence()throws Exception{
    Owner o=media();call(InfinityExtendedBackgroundService.class,"dispatchMiniCommand",grantGeneration(),3);assertEquals(3,o.command);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(service,"mMediaSession"));
  }
  @Test public void removedTaskPausesOwnerAndReleasesMediaSession()throws Exception{
    Owner o=media();service.onTaskRemoved(new Intent());assertFalse(o.available);assertEquals(1,o.unavailable);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(service,"mMediaSession"));
  }
  @Test public void naturalEndCannotLeavePlayingNotification()throws Exception{
    Owner o=media();o.available=false;InfinityExtendedBackgroundService.refreshMiniPlayback(o);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(service,"mMediaSession"));
  }
  @Test public void mediaNotificationTargetsExistingCobraActivity()throws Exception{
    media();PendingIntent pending=(PendingIntent)call(service,"miniOpenPendingIntent");Intent intent=Shadows.shadowOf(pending).getSavedIntent();assertEquals(InfinityLiveActivity.class.getName(),intent.getComponent().getClassName());assertTrue((intent.getFlags()&Intent.FLAG_ACTIVITY_SINGLE_TOP)!=0);
  }
  View anchoredSheet(int width,int height)throws Exception{
    FrameLayout root=new FrameLayout(a);a.setContentView(root);set(a,"mPlayerOverlay",null);set(a,"mMultiOverlay",null);
    FrameLayout pane=new FrameLayout(a);FrameLayout.LayoutParams pp=new FrameLayout.LayoutParams(width-48,210);pp.leftMargin=24;pp.topMargin=100;root.addView(pane,pp);
    Button anchor=new Button(a);anchor.setText("Options");FrameLayout.LayoutParams bp=new FrameLayout.LayoutParams(64,48,Gravity.RIGHT|Gravity.BOTTOM);pane.addView(anchor,bp);
    set(a,"mCobraPreviewHost",pane);ui.measure(a,width,height);set(a,"mCobraNextSheetAnchor",anchor);
    LinearLayout rows=(LinearLayout)call(a,"cobraOpenSheet","Options","Current channel","channel");
    for(int i=0;i<12;i++){TextView row=new TextView(a);row.setText("Option "+i);rows.addView(row,new LinearLayout.LayoutParams(-1,56));}
    layout(width,height);return anchor;
  }
  void layout(int width,int height)throws Exception{
    for(int i=0;i<8;i++){ui.measure(a,width,height);Shadows.shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));
      View sheet=(View)get(a,"mCobraActionSheet");if(sheet!=null)sheet.getViewTreeObserver().dispatchOnGlobalLayout();}
  }
  void assertAnchored()throws Exception{
    FrameLayout scrim=(FrameLayout)get(a,"mCobraActionSheet");LinearLayout panel=(LinearLayout)get(a,"mCobraSheetPanel");View pane=(View)get(a,"mCobraSheetPane");
    assertNotNull(panel);int[] safe=(int[])call(a,"cobraSheetSafeBounds",scrim),pb=(int[])call(a,"cobraLocalBounds",pane,scrim);
    assertTrue(panel.getLeft()>=Math.max(safe[0],pb[0]));assertTrue(panel.getRight()<=Math.min(safe[2],pb[2]));
    assertTrue(panel.getTop()>=safe[1]);assertTrue(panel.getBottom()<=safe[3]);assertEquals(1f,panel.getAlpha(),0f);
    FrameLayout.LayoutParams lp=(FrameLayout.LayoutParams)panel.getLayoutParams();assertEquals(Gravity.TOP|Gravity.LEFT,lp.gravity);
  }
  @Test public void previewOptionsAnchorInNarrowWindow()throws Exception{anchoredSheet(360,740);assertAnchored();}
  @Test public void previewOptionsAnchorInWideWindow()throws Exception{anchoredSheet(1100,700);assertAnchored();}
  @Test public void nestedMenuRetainsOriginalButtonAnchor()throws Exception{
    View anchor=anchoredSheet(412,915);LinearLayout row=(LinearLayout)call(a,"cobraSheetRow","settings","More",null,false,true,(Runnable)()->{
      try{call(a,"cobraOpenSheet","Nested","Same pane","nested");}catch(Exception error){throw new AssertionError(error);}
    });row.performClick();layout(412,915);assertSame(anchor,get(a,"mCobraSheetAnchor"));assertAnchored();assertNull(get(a,"mCobraNextSheetAnchor"));
  }
  @Test public void dismissingMenuRemovesLayoutObserverAndAnchor()throws Exception{
    anchoredSheet(412,915);call(a,"closeCobraActionSheet");assertNull(get(a,"mCobraSheetLayoutListener"));assertNull(get(a,"mCobraSheetAnchor"));assertNull(get(a,"mCobraActionSheet"));
  }
}
