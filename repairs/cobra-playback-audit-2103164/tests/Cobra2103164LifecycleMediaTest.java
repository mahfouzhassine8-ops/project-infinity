package com.projectinfinity.kodi;

import android.app.*;
import android.content.*;
import android.os.*;
import android.media.session.*;
import android.view.*;
import android.widget.*;
import androidx.media3.common.Player;
import java.util.*;
import java.lang.reflect.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.android.controller.ServiceController;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.Cobra2103164RegressionTest.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103164LifecycleMediaTest {
  final Cobra2103164RegressionTest f=new Cobra2103164RegressionTest();
  final List<ServiceController<InfinityExtendedBackgroundService>> services=new ArrayList<>();
  Context app;
  @Before public void before(){
    f.before();app=RuntimeEnvironment.getApplication();InfinityExtendedBackgroundService.stopForExit(app);
    while(Shadows.shadowOf((Application)app).getNextStartedService()!=null){}
  }
  @After public void after(){
    for(ServiceController<InfinityExtendedBackgroundService> s:services)s.destroy();
    services.clear();InfinityExtendedBackgroundService.stopForExit(app);
  }
  void frame(){Shadows.shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));}
  InfinityExtendedBackgroundService service(Intent intent){
    ServiceController<InfinityExtendedBackgroundService> c=Robolectric.buildService(InfinityExtendedBackgroundService.class).create();services.add(c);
    c.get().onStartCommand(intent,0,1);return c.get();
  }
  Intent miniIntent(){
    Intent i;while((i=Shadows.shadowOf((Application)app).getNextStartedService())!=null)if(i.getAction()!=null&&i.getAction().endsWith("MINI_BACKGROUND_START"))return i;
    throw new AssertionError("A real foreground mini handoff must have requested the service");
  }
  Cobra2103164RegressionTest.Video preview(InfinityLiveActivity a)throws Exception{
    call(a,"cobraOpenLiveTv");f.ui.measure(a,412,915);
    Cobra2103164RegressionTest.Video v=new Cobra2103164RegressionTest.Video(a);
    put(a,"mCobraPreviewPlayer",v.player);put(a,"mGuidePreviewChannel",((List<?>)get(a,"mChannels")).get(0));
    ((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_mini_background_playback",true).commit();return v;
  }
  MediaSession session(InfinityExtendedBackgroundService s)throws Exception{return (MediaSession)callGet(s,"mMediaSession");}
  Object callGet(Object owner,String name)throws Exception{Field field=owner.getClass().getDeclaredField(name);field.setAccessible(true);return field.get(owner);}
  Notification notification(){return ((NotificationManager)app.getSystemService(Context.NOTIFICATION_SERVICE)).getActiveNotifications()[0].getNotification();}

  @Test public void nativePipExpansionKeepsSameFullscreenVideo()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=f.fullscreen(a,412,915);Object overlay=get(a,"mPlayerOverlay");
      a.onPictureInPictureModeChanged(true,a.getResources().getConfiguration());call(a,"onPause");
      assertTrue("Visible PiP must keep playing while paused",v.ready);
      a.onPictureInPictureModeChanged(false,a.getResources().getConfiguration());call(a,"onResume");
      assertSame(overlay,get(a,"mPlayerOverlay"));assertSame(v.player,get(a,"mPlayer"));assertTrue(v.ready);
      assertFalse(v.commands.contains("release"));assertFalse(v.commands.contains("prepare"));
    }finally{f.clean(a);}
  }
  @Test public void ordinaryBackgroundPauseStillResumesWhenNoPipWasEntered()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=f.fullscreen(a,412,915);call(a,"onPause");call(a,"onStop");assertFalse(v.ready);
      call(a,"onResume");assertTrue(v.ready);assertSame(v.player,get(a,"mPlayer"));
    }finally{f.clean(a);}
  }
  @Test public void dismissedPipCannotRestartFromLatePlayAndRepeatCallbacks()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=f.fullscreen(a,412,915);
      a.onPictureInPictureModeChanged(true,a.getResources().getConfiguration());call(a,"onPause");call(a,"onStop");
      call(a,"startCobraPlayer",v.player);a.onPictureInPictureModeChanged(false,a.getResources().getConfiguration());call(a,"onStop");call(a,"onResume");
      assertFalse(v.ready);assertNull(get(a,"mPlayerOverlay"));assertTrue(((Map<?,?>)get(a,"mBackgroundResumePlayers")).isEmpty());
      assertEquals("Dispose once rather than repeated stops/restarts",1,Collections.frequency(v.commands,"release"));
    }finally{f.clean(a);}
  }
  @Test public void explicitCobraBrowseIntentIsConsumedOnceAndLockCannotTrapNavigation()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=f.fullscreen(a,412,915);put(a,"mCobraPlayerLocked",true);
      Intent intent=new Intent(a,InfinityLiveActivity.class).putExtra("cobra_open_browse",true);call(a,"onNewIntent",intent);call(a,"onResume");
      assertNull(get(a,"mPlayerOverlay"));assertFalse(intent.hasExtra("cobra_open_browse"));assertSame(v.player,get(a,"mCobraPreviewPlayer"));
      Object channel=((List<?>)get(a,"mChannels")).get(0);put(a,"mPlayer",v.player);put(a,"mPlaying",channel);call(a,"openPlayerOverlay",channel);
      Object overlay=get(a,"mPlayerOverlay");call(a,"onResume");assertSame("Old consumed intent must not keep minimizing",overlay,get(a,"mPlayerOverlay"));
    }finally{f.clean(a);}
  }
  @Test public void chooserCobraLaunchIncludesBrowseRequestButInfinityDoesNot()throws Exception{
    ExperienceChooserUiTest.reflect();ExperienceChooserUiTest h=new ExperienceChooserUiTest();
    try{
      Splash cobra=h.activity();call(cobra,"launchInfinityExperience","live");Intent ci=Shadows.shadowOf(cobra).getNextStartedActivity();assertTrue(ci.getBooleanExtra("cobra_open_browse",false));assertEquals(InfinityLiveActivity.class.getName(),ci.getComponent().getClassName());
      Splash infinity=h.activity();call(infinity,"launchInfinityExperience","infinity");Intent ii=Shadows.shadowOf(infinity).getNextStartedActivity();assertFalse(ii.hasExtra("cobra_open_browse"));
    }finally{h.closeWindows();}
  }
  @Test public void miniHandoffKeepsExactPlayerThenForegroundReturnDoesNotRestart()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);Object texture=get(a,"mCobraPreviewTexture");
      call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());call(a,"onPause");call(a,"onStop");
      assertTrue(v.ready);assertTrue(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNotNull(session(s));
      assertTrue(notification().contentIntent!=null);Intent open=Shadows.shadowOf(notification().contentIntent).getSavedIntent();
      assertEquals(InfinityLiveActivity.class.getName(),open.getComponent().getClassName());assertTrue(open.getBooleanExtra("cobra_open_browse",false));
      call(a,"onNewIntent",open);call(a,"onResume");assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(session(s));
      assertTrue(v.ready);assertSame(v.player,get(a,"mCobraPreviewPlayer"));assertSame(texture,get(a,"mCobraPreviewTexture"));
      assertFalse(v.commands.contains("prepare"));assertFalse(v.commands.contains("release"));assertFalse(v.commands.contains("pause"));
    }finally{f.clean(a);}
  }
  @Test public void miniOffPausesAndOnStopAloneNeverStartsForegroundMedia()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);
      ((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_mini_background_playback",false).commit();
      call(a,"onUserLeaveHint");assertNull(Shadows.shadowOf((Application)app).getNextStartedService());
      call(a,"onPause");call(a,"onStop");assertFalse(v.ready);assertFalse((Boolean)get(a,"mCobraMiniBackgroundActive"));
      assertNull("onStop cannot start a service after foreground eligibility is gone",Shadows.shadowOf((Application)app).getNextStartedService());
    }finally{f.clean(a);}
  }
  @Test public void fullscreenCannotAcquireMiniBackgroundEvenWhenSettingIsOn()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      f.fullscreen(a,412,915);((SharedPreferences)get(a,"mPrefs")).edit().putBoolean("cobra_mini_background_playback",true).commit();
      assertFalse((Boolean)call(a,"cobraBeginMiniBackgroundPlayback"));assertNull(Shadows.shadowOf((Application)app).getNextStartedService());
    }finally{f.clean(a);}
  }
  @Test public void miniWithSettingOnButNoForegroundHandoffFailsClosedAtStop()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onPause");call(a,"onStop");
      assertFalse(v.ready);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(Shadows.shadowOf((Application)app).getNextStartedService());
    }finally{f.clean(a);}
  }
  @Test public void permissionRevocationBeforePromotionStopsUnnotifiedAudio()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");Intent request=miniIntent();
      Shadows.shadowOf((Application)app).denyPermissions("android.permission.POST_NOTIFICATIONS");
      service(request);call(a,"onPause");call(a,"onStop");assertFalse(v.ready);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertTrue(((Map<?,?>)get(a,"mBackgroundResumePlayers")).isEmpty());
    }finally{f.clean(a);}
  }
  @Test public void taskRemovalStopsTheRealMiniOwnerNotJustTheNotification()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());call(a,"onPause");call(a,"onStop");
      s.onTaskRemoved(new Intent());assertFalse(v.ready);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(get(a,"mCobraPreviewPlayer"));
      call(a,"onResume");assertFalse(v.ready);assertTrue(((Map<?,?>)get(a,"mBackgroundResumePlayers")).isEmpty());
    }finally{f.clean(a);}
  }
  @Test public void notificationPausePlayAndStopAreBoundToTheSameSession()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());call(a,"onPause");call(a,"onStop");
      Notification n=notification();assertEquals(2,n.actions.length);
      s.onStartCommand(Shadows.shadowOf(n.actions[0].actionIntent).getSavedIntent(),0,2);assertFalse(v.ready);
      assertEquals("Play",notification().actions[0].title.toString());
      s.onStartCommand(Shadows.shadowOf(notification().actions[0].actionIntent).getSavedIntent(),0,3);assertTrue(v.ready);assertSame(v.player,get(a,"mCobraPreviewPlayer"));
      s.onStartCommand(Shadows.shadowOf(notification().actions[1].actionIntent).getSavedIntent(),0,4);assertFalse(v.ready);assertNull(get(a,"mCobraPreviewPlayer"));
      assertNull(session(s));assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
    }finally{f.clean(a);}
  }
  @Test public void lateStartAfterReturnCannotResurrectBackgroundPresence()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");Intent request=miniIntent();call(a,"onResume");
      InfinityExtendedBackgroundService s=service(request);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(session(s));
      assertTrue("Foreground return retains player",v.ready);
    }finally{f.clean(a);}
  }
  @Test public void oldStartCannotStopNewerAuthorizedMiniOwner()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");Intent old=miniIntent();call(a,"onResume");
      call(a,"onUserLeaveHint");Intent current=miniIntent();InfinityExtendedBackgroundService s=service(old);s.onStartCommand(current,0,2);
      assertTrue(v.ready);assertTrue(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertTrue((Boolean)call(a,"cobraMiniBackgroundStillOwned"));
    }finally{f.clean(a);}
  }
  @Test public void noOwnerAfterProcessRestartCannotCreateFakePlayingSession()throws Exception{
    InfinityExtendedBackgroundService s=service(new Intent(app,InfinityExtendedBackgroundService.class)
        .setAction("com.projectinfinity.kodi.action.MINI_BACKGROUND_START").putExtra("mini_generation",555));
    assertNull(session(s));assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
  }
  @Test public void unexpectedServiceDestructionSilencesMiniPlayer()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());
      call(a,"onPause");call(a,"onStop");s.onDestroy();assertFalse(v.ready);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
    }finally{f.clean(a);}
  }
  @Test public void extendedContinuityRemainsSeparateAfterMiniStop()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);app.getSharedPreferences("infinity_runtime",0).edit().putBoolean("extended_background",true).commit();
      call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());
      s.onStartCommand(Shadows.shadowOf(notification().actions[1].actionIntent).getSavedIntent(),0,3);
      assertFalse(v.ready);assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertTrue(InfinityExtendedBackgroundService.isEnabled(app));assertTrue(InfinityExtendedBackgroundService.isRunning());assertNull(session(s));
    }finally{f.clean(a);}
  }
  @Test public void platformMediaSessionCallbacksAndStateUseActualPlayer()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());call(a,"onPause");call(a,"onStop");
      MediaSession ms=session(s);
      // Use the real framework callback dispatcher, not direct invocation of our callbacks.
      // Binder/system-UI delivery itself remains physical-device acceptance.
      MediaSessionManager.RemoteUserInfo user=new MediaSessionManager.RemoteUserInfo(a.getPackageName(),123,456);
      call(ms,"dispatchPause",user);for(int n=0;n<5;n++)frame();assertFalse(v.ready);
      PlaybackState paused=(PlaybackState)callGet(ms,"mPlaybackState");assertEquals(PlaybackState.STATE_PAUSED,paused.getState());assertEquals(v.position,paused.getPosition());
      call(ms,"dispatchPlay",user);for(int n=0;n<5;n++)frame();assertTrue(v.ready);
      assertEquals(PlaybackState.STATE_PLAYING,((PlaybackState)callGet(ms,"mPlaybackState")).getState());
      call(ms,"dispatchStop",user);for(int n=0;n<5;n++)frame();assertFalse(v.ready);assertNull(session(s));
    }finally{f.clean(a);}
  }
  @Test public void pausedAndBufferingMediaStatesAreNotFalselyAlwaysPlaying()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);v.state=Player.STATE_BUFFERING;call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());
      assertEquals(PlaybackState.STATE_BUFFERING,((PlaybackState)callGet(session(s),"mPlaybackState")).getState());
      v.ready=false;call(s,"ensureMediaSession");assertEquals(PlaybackState.STATE_PAUSED,((PlaybackState)callGet(session(s),"mPlaybackState")).getState());
      v.state=Player.STATE_ENDED;((Runnable)callGet(s,"mMiniRefresh")).run();assertFalse(InfinityExtendedBackgroundService.isMiniPlaybackRunning());assertNull(session(s));
    }finally{f.clean(a);}
  }
  @Test public void lateNotificationStopCannotStopAReplacementOwner()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);call(a,"onUserLeaveHint");InfinityExtendedBackgroundService s=service(miniIntent());
      Intent oldStop=Shadows.shadowOf(notification().actions[1].actionIntent).getSavedIntent();
      call(a,"onResume");call(a,"onUserLeaveHint");s.onStartCommand(miniIntent(),0,2);
      s.onStartCommand(oldStop,0,3);assertTrue(v.ready);assertTrue(InfinityExtendedBackgroundService.isMiniPlaybackRunning());
    }finally{f.clean(a);}
  }
  @Test public void terminalBackHandsMiniToServiceWhileForeground()throws Exception{
    InfinityLiveActivity a=f.activity();try{
      Cobra2103164RegressionTest.Video v=preview(a);put(a,"mCobraInternalScreen","root");put(a,"mCobraGuideStyle","grid");put(a,"mCobraModeLayout",null);
      call(a,"onBackPressed");Intent request=miniIntent();service(request);call(a,"onPause");call(a,"onStop");assertTrue(v.ready);
    }finally{f.clean(a);}
  }

}
