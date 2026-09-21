package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Intent;
import android.content.res.Configuration;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.Handler;
import android.os.Looper;
import android.view.KeyEvent;
import android.view.View;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.Proxy;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Real Activity/MediaSession callback wiring with controlled Media3 players.
 * Does not emulate Samsung SystemUI, a decoder, call routing or physical PiP. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103203PipControlsTest {
  Cobra2103202LifecycleTest f;InfinityLiveActivity a;Cobra2103202LifecycleTest.State s;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  Object call(String n,Object...args)throws Exception{return CobraNavigationUiTest.call(a,n,args);}
  @Before public void before()throws Exception{f=new Cobra2103202LifecycleTest();f.before();a=f.a;}
  @After public void after()throws Exception{if(a!=null)call("cobraReleasePipMediaSession");if(f!=null)f.after();}
  void single()throws Exception{s=f.single();f.resumePolicy();}
  void enter()throws Exception{put(a,"mInPictureInPicture",true);CobraNavigationUiTest.call(get(a,"mCobraPlaybackPolicy"),"pipChanged",true);call("cobraUpdatePipMediaSession");assertNotNull(get(a,"mCobraPipMediaSession"));}
  MediaSession session()throws Exception{return (MediaSession)get(a,"mCobraPipMediaSession");}
  Object binding()throws Exception{return ((Map<?,?>)get(a,"mCobraPlayerBindings")).get(get(a,"mPlayer"));}
  MediaSession.Callback callback()throws Exception{return (MediaSession.Callback)get(get(session(),"mCallback"),"mCallback");}
  PlaybackState state()throws Exception{return (PlaybackState)call("cobraPipPlaybackState",get(a,"mPlayer"));}

  @Test public void controlsExistOnlyInPipAndAdvertiseOnlyRequestedTransport()throws Exception{
    single();call("configureCobraPip",true);assertNull(session());enter();assertTrue(session().isActive());
    assertEquals(PlaybackState.ACTION_PLAY|PlaybackState.ACTION_PAUSE|PlaybackState.ACTION_PLAY_PAUSE,state().getActions());
    assertEquals(PlaybackState.STATE_PLAYING,state().getState());assertEquals(1f,state().getPlaybackSpeed(),0f);
  }
  @Test public void pauseThenPlayControlsSamePlayerWithoutDecoderOrSurfaceReplacement()throws Exception{
    single();enter();MediaSession media=session();View texture=(View)get(a,"mPlayerTexture");MediaSession.Callback command=callback();
    command.onPause();assertFalse(s.requested);assertSame(media,session());assertTrue(media.isActive());assertEquals(PlaybackState.STATE_PAUSED,state().getState());
    command.onPlay();assertTrue(s.requested);assertSame(s.player,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));assertEquals(0,s.releases);assertEquals(0,s.prepares);
  }
  @Test public void userPauseRemovesBackgroundResumeAndInvalidatesPendingRetry()throws Exception{
    single();enter();Map<ExoPlayer,Boolean> resume=(Map<ExoPlayer,Boolean>)get(a,"mBackgroundResumePlayers");resume.put(s.player,true);long epoch=(Long)get(get(a,"mCobraPlaybackPolicy"),"epoch");
    callback().onPause();assertFalse(resume.containsKey(s.player));assertTrue((Long)get(get(a,"mCobraPlaybackPolicy"),"epoch")>epoch);assertFalse(s.requested);
  }
  @Test public void bufferingStateStillAdvertisesPauseWithoutPretendingVideoIsPlaying()throws Exception{
    single();ExoPlayer buffering=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},(p,m,v)->m.getName().equals("getPlaybackState")?Player.STATE_BUFFERING:m.getName().equals("isPlaying")?false:s.invoke(p,m,v));
    PlaybackState state=(PlaybackState)call("cobraPipPlaybackState",buffering);assertEquals(PlaybackState.STATE_BUFFERING,state.getState());assertEquals(0f,state.getPlaybackSpeed(),0f);assertTrue((state.getActions()&PlaybackState.ACTION_PAUSE)!=0);
  }
  @Test public void playWhenReadyCallbackUpdatesNativeSessionStateWithoutReplacingSession()throws Exception{
    single();enter();MediaSession media=session();s.requested=false;CobraNavigationUiTest.call(binding(),"onPlayWhenReadyChanged",false,Player.PLAY_WHEN_READY_CHANGE_REASON_USER_REQUEST);
    assertSame(media,session());assertEquals(PlaybackState.STATE_PAUSED,((PlaybackState)get(media,"mPlaybackState")).getState());
    s.requested=true;CobraNavigationUiTest.call(binding(),"onIsPlayingChanged",true);assertEquals(PlaybackState.STATE_PLAYING,((PlaybackState)get(media,"mPlaybackState")).getState());
  }
  @Test public void standardPlayPauseMediaButtonTogglesThroughTheBoundCallback()throws Exception{
    single();enter();assertNotNull(callback());
    Intent key=new Intent(Intent.ACTION_MEDIA_BUTTON).putExtra(Intent.EXTRA_KEY_EVENT,new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE));
    android.media.session.MediaSessionManager.RemoteUserInfo controller=new android.media.session.MediaSessionManager.RemoteUserInfo("fixture",123,123);
    CobraNavigationUiTest.call(session(),"dispatchMediaButton",controller,key);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(1));assertFalse(s.requested);
    CobraNavigationUiTest.call(session(),"dispatchMediaButton",controller,key);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(1));assertTrue(s.requested);
  }
  @Test public void exitedPipRejectsOldCommandsAndReleasesMediaPresence()throws Exception{
    single();enter();MediaSession old=session();MediaSession.Callback command=callback();put(a,"mInPictureInPicture",false);call("cobraUpdatePipMediaSession");assertNull(session());assertFalse(old.isActive());command.onPause();assertTrue(s.requested);
  }
  @Test public void ownerReplacementRejectsBothOldPlayerAndOldGeneration()throws Exception{
    single();enter();MediaSession.Callback old=callback();Cobra2103202LifecycleTest.State original=s;s=f.single();call("cobraUpdatePipMediaSession");
    old.onPause();assertTrue(original.requested);assertTrue(s.requested);callback().onPause();assertFalse(s.requested);
  }
  @Test public void staleBindingCannotControlSamePlayerSlot()throws Exception{
    single();enter();MediaSession.Callback old=callback();put(binding(),"closed",true);old.onPause();assertTrue(s.requested);call("cobraUpdatePipMediaSession");assertNull(session());
  }
  @Test public void profileChangeRejectsPreviouslyIssuedCommands()throws Exception{
    single();enter();MediaSession.Callback old=callback();InfinityCobraFeatureRuntime features=(InfinityCobraFeatureRuntime)get(a,"mFeatures");String profile=features.createProfile("Other","",false);assertTrue(features.unlockAndSelectProfile(profile,""));old.onPause();assertTrue(s.requested);
  }
  @Test public void disposalRevokesMediaSessionBeforePlayerRelease()throws Exception{
    single();enter();MediaSession.Callback old=callback();call("cobraDisposePlayer",s.player);assertNull(session());assertEquals(1,s.releases);old.onPause();assertTrue(s.requested);
  }
  @Test public void dismissalStopsOwnerAndRejectsPlayFromCachedPipWindow()throws Exception{
    single();enter();MediaSession.Callback old=callback();call("cobraHaltHiddenPlayback");assertNull(session());assertFalse(s.requested);old.onPlay();assertFalse(s.requested);assertTrue(((Map<?,?>)get(a,"mBackgroundResumePlayers")).isEmpty());
  }
  @Test public void hiddenOnStopCannotLeaveAnActivePipMediaSession()throws Exception{
    single();enter();MediaSession.Callback old=callback();call("onStop");assertNull(session());assertFalse(s.requested);old.onPlay();assertFalse(s.requested);
  }
  @Test public void pausedOwnerRemainsControllableEvenWhenAutoEntryIsDisabled()throws Exception{
    single();enter();callback().onPause();assertEquals(false,call("cobraWantsFullscreenPip"));call("configureCobraPip",false);assertNotNull(session());assertTrue(session().isActive());callback().onPlay();assertTrue(s.requested);
  }
  @Test public void backgroundMediaOwnershipCannotOverlapPipControls()throws Exception{
    single();enter();put(a,"mCobraMiniBackgroundActive",true);call("cobraUpdatePipMediaSession");assertNull(session());put(a,"mCobraMiniBackgroundActive",false);call("cobraUpdatePipMediaSession");assertNotNull(session());
  }
  @Test public void multiviewPipPauseSurvivesReturnWithoutPausingHealthyPeers()throws Exception{
    f.multi(3);f.states.get(2).requested=false;call("cobraPrepareMultiForPip");f.resumePolicy();enter();callback().onPause();
    assertFalse((Boolean)((Map<?,?>)get(a,"mCobraPipMultiRequested")).get(get(a,"mCobraPipMultiAudio")));
    put(a,"mInPictureInPicture",false);call("cobraUpdatePipMediaSession");f.resumePolicy();call("cobraRestoreMultiAfterPip");ExoPlayer[] restored=(ExoPlayer[])get(a,"mMultiPlayers");
    assertEquals(3,restored.length);assertSame(f.states.get(1).player,restored[1]);assertFalse(restored[1].getPlayWhenReady());assertFalse(restored[2].getPlayWhenReady());assertTrue(restored[0].getPlayWhenReady());assertEquals(1,get(a,"mAudioTile"));
  }
  @Test public void multiviewPipPlayUpdatesOnlySavedOwnerIntent()throws Exception{
    f.multi(3);f.states.get(2).requested=false;call("cobraPrepareMultiForPip");f.resumePolicy();enter();MediaSession.Callback command=callback();command.onPause();command.onPlay();
    Map<?,?> saved=(Map<?,?>)get(a,"mCobraPipMultiRequested");assertEquals(true,saved.get(get(a,"mCobraPipMultiAudio")));assertEquals(false,saved.get(get(f.channels.get(2),"id")));
  }
  @Test public void repeatedRoundTripsRevokeOldTokensWithoutReleasingPlayer()throws Exception{
    single();for(int i=0;i<4;i++){enter();MediaSession.Callback old=callback();put(a,"mInPictureInPicture",false);call("cobraUpdatePipMediaSession");enter();old.onPause();assertTrue(s.requested);put(a,"mInPictureInPicture",false);call("cobraUpdatePipMediaSession");}assertEquals(0,s.releases);assertEquals(0,s.prepares);
  }
  @Test public void diagnosticsReportActualSessionButDoNotClaimCallTimeAudibility()throws Exception{
    single();enter();JSONObject snapshot=new JSONObject((String)call("cobraFreshHealthSnapshot"));assertTrue(snapshot.getBoolean("pip_media_session_active"));assertEquals(get(a,"mCobraPipMediaGeneration"),snapshot.getLong("pip_media_generation"));assertEquals("",snapshot.getString("pip_media_error"));assertEquals("not_observed_by_app",snapshot.getString("call_time_audibility"));
    put(a,"mInPictureInPicture",false);call("cobraUpdatePipMediaSession");assertFalse(new JSONObject((String)call("cobraFreshHealthSnapshot")).getBoolean("pip_media_session_active"));
  }
  @Test @Config(sdk=26) public void androidEightPipUsesTheSameScopedTransport()throws Exception{single();enter();callback().onPause();assertFalse(s.requested);callback().onPlay();assertTrue(s.requested);}
}
