package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.media.AudioManager;
import android.media.AudioFocusRequest;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.Looper;
import android.view.View;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowAudioManager;
import static org.junit.Assert.*;

/** Actual Activity/settings/AudioManager/MediaSession wiring with controlled Media3
 * players. No test here establishes physical telephony, routing or audibility. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103206MediaCallsTest {
  Cobra2103202LifecycleTest f; InfinityLiveActivity a; AudioManager manager; ShadowAudioManager audio;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(a,n,v);}
  @Before public void before()throws Exception{
    f=new Cobra2103202LifecycleTest();f.before();a=f.a;
    manager=(AudioManager)a.getSystemService(Context.AUDIO_SERVICE);audio=Shadows.shadowOf(manager);
    manager.setMode(AudioManager.MODE_NORMAL);audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_GRANTED);
    f.prefs.edit().remove("cobra_media_during_calls").commit();
  }
  @After public void after()throws Exception{if(a!=null)call("cobraReleasePipMediaSession");if(f!=null)f.after();}
  void manual(){f.prefs.edit().putString("cobra_media_during_calls","manual").commit();}
  AudioManager.OnAudioFocusChangeListener listener()throws Exception{return (AudioManager.OnAudioFocusChangeListener)get(a,"mCobraAudioFocusListener");}
  Object request()throws Exception{return get(a,"mCobraAudioFocusRequest");}
  void mode(int value)throws Exception{
    manager.setMode(value);
    Object owner=get(a,"mCobraAudioFocusPlayer");
    if(owner!=null)call("cobraHandleAudioMode",owner,get(a,"mCobraAudioFocusGeneration"),value);
  }
  Cobra2103202LifecycleTest.State playing()throws Exception{Cobra2103202LifecycleTest.State s=f.single();call("cobraUserPlay",s.player);return s;}
  void interrupt()throws Exception{mode(AudioManager.MODE_IN_CALL);listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);}
  void unchanged(Cobra2103202LifecycleTest.State s)throws Exception{assertSame(s.player,get(a,"mPlayer"));assertEquals(0,s.prepares);assertEquals(0,s.releases);}
  View row(String tag){View v=a.getWindow().getDecorView().findViewWithTag(tag);assertNotNull(tag,v);return v;}

  @Test public void defaultAndMalformedSettingBothUseNormalAndroidBehavior()throws Exception{
    assertEquals(false,call("cobraManualCallResumeEnabled"));f.prefs.edit().putString("cobra_media_during_calls","broken").commit();assertEquals(false,call("cobraManualCallResumeEnabled"));
    assertEquals("Normal Android Behavior",call("cobraMediaDuringCallsLabel"));
  }
  @Test public void noCallPlayUsesOriginalMediaAttributesAndDelayedFocus()throws Exception{
    Cobra2103202LifecycleTest.State s=playing();AudioFocusRequest r=(AudioFocusRequest)request();
    assertEquals(android.media.AudioAttributes.USAGE_MEDIA,r.getAudioAttributes().getUsage());assertEquals(android.media.AudioAttributes.CONTENT_TYPE_MOVIE,r.getAudioAttributes().getContentType());assertTrue(r.acceptsDelayedFocusGain());assertEquals(1f,s.volume,0f);unchanged(s);
  }
  @Test public void incomingCallNeverRequestsFocusOrRestartsPlayerEvenWhenOptedIn()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();Object original=request();interrupt();
    assertSame(original,request());assertTrue(s.requested);assertEquals(0f,s.volume,0f);assertEquals(false,get(a,"mCobraManualCallResume"));unchanged(s);
  }
  @Test public void defaultPlayDuringKnownCallWaitsOnExistingAndroidRequest()throws Exception{
    Cobra2103202LifecycleTest.State s=playing();Object r=request();interrupt();call("cobraUserPlay",s.player);
    assertSame(r,request());assertEquals(0f,s.volume,0f);assertEquals(false,get(a,"mCobraManualCallResume"));unchanged(s);
  }
  @Test public void optInOneTapPlayRetriesAndKeepsPlayerSurfaceChannelTimeshift()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();put(a,"mCobraTimeshiftPlayer",s.player);Object channel=get(a,"mPlaying"),surface=get(a,"mPlayerTexture"),r=request();interrupt();
    assertEquals("Play",row("cobra_player_play_pause").getContentDescription());call("toggleCobraPlayerPlayPause");
    assertNotSame(r,request());assertTrue(s.requested);assertEquals(1f,s.volume,0f);assertEquals("Pause",row("cobra_player_play_pause").getContentDescription());
    assertSame(channel,get(a,"mPlaying"));assertSame(surface,get(a,"mPlayerTexture"));assertSame(s.player,get(a,"mCobraTimeshiftPlayer"));unchanged(s);
  }
  @Test public void deniedManualRequestRemainsMutedAndNeverReprepares()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_FAILED);call("cobraUserPlay",s.player);
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);assertEquals("denied",get(a,"mCobraManualCallAttempt"));unchanged(s);
  }
  @Test public void delayedManualRequestOnlyUnmutesOnAcceptedGrant()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_DELAYED);call("cobraUserPlay",s.player);
    assertEquals(0f,s.volume,0f);assertEquals("delayed",get(a,"mCobraManualCallAttempt"));listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(1f,s.volume,0f);unchanged(s);
  }
  @Test public void pauseBeforeDelayedGrantDoesNotResumePlayer()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_DELAYED);call("cobraUserPlay",s.player);Object r=request();call("toggleCobraPlayerPlayPause");assertFalse(s.requested);assertSame(r,request());
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);mode(AudioManager.MODE_NORMAL);assertFalse(s.requested);unchanged(s);
  }
  @Test public void automaticRecoveryAndHandoffCannotRenewFocusDuringCall()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();Object r=request();call("startCobraPlayer",s.player);call("cobraClaimAudioFocus",s.player);
    assertSame(r,request());assertEquals(0f,s.volume,0f);unchanged(s);
  }
  @Test public void callEndWithoutFocusGainDoesNotInventAudioPermission()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();mode(AudioManager.MODE_NORMAL);assertEquals(0f,s.volume,0f);unchanged(s);
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(1f,s.volume,0f);unchanged(s);
  }
  @Test public void callEndAfterManualGrantDoesNotRenewOrRestartAnything()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();call("cobraUserPlay",s.player);Object r=request();mode(AudioManager.MODE_NORMAL);
    assertSame(r,request());assertEquals(1f,s.volume,0f);assertEquals(false,get(a,"mCobraManualCallResume"));unchanged(s);
  }
  @Test public void switchingOffDuringCallMutesAndLateGainCannotReenableIt()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();call("cobraUserPlay",s.player);call("cobraShowMediaDuringCalls",f.channels.get(0));row("cobra-media-during-calls:normal").performClick();
    assertEquals(false,call("cobraManualCallResumeEnabled"));assertEquals(0f,s.volume,0f);listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);unchanged(s);
  }
  @Test public void turningOnDuringCallNeverResumesUntilPlay()throws Exception{
    Cobra2103202LifecycleTest.State s=playing();interrupt();Object r=request();call("cobraShowMediaDuringCalls",f.channels.get(0));row("cobra-media-during-calls:manual").performClick();
    assertSame(r,request());assertEquals(0f,s.volume,0f);assertEquals(false,get(a,"mCobraManualCallResume"));unchanged(s);
  }
  @Test public void selectedSettingPersistsAndReopeningUsesStoredValue()throws Exception{
    f.single();call("cobraShowChannelPreferences",f.channels.get(0));row("cobra-media-during-calls").performClick();row("cobra-media-during-calls:manual").performClick();
    assertEquals("manual",f.prefs.getString("cobra_media_during_calls",""));assertEquals("channel-playback",get(a,"mCobraSheetKind"));
    call("cobraShowMediaDuringCalls",f.channels.get(1));assertEquals("Allow When Manually Resumed",call("cobraMediaDuringCallsLabel"));row("cobra-media-during-calls:normal").performClick();assertEquals("normal",f.prefs.getString("cobra_media_during_calls",""));
  }
  @Test public void ringingIsNeverEligibleForManualCallResume()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();mode(AudioManager.MODE_RINGTONE);Object r=request();call("cobraUserPlay",s.player);
    assertSame(r,request());assertEquals(false,call("cobraCallResumeAvailable",s.player));assertEquals(0f,s.volume,0f);unchanged(s);
  }
  @Test public void communicationModeSupportsOnlyExplicitOptIn()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();mode(AudioManager.MODE_IN_COMMUNICATION);assertEquals(0f,s.volume,0f);call("cobraUserPlay",s.player);assertEquals(1f,s.volume,0f);unchanged(s);
  }
  @Test public void secondFocusInterruptionRevokesPriorManualIntent()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();call("cobraUserPlay",s.player);listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);assertEquals(false,get(a,"mCobraManualCallResume"));unchanged(s);
  }
  @Test public void staleFocusAndModeCallbacksCannotAffectNewRequest()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();AudioManager.OnAudioFocusChangeListener old=listener();long generation=(Long)get(a,"mCobraAudioFocusGeneration");interrupt();call("cobraUserPlay",s.player);
    old.onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS);call("cobraHandleAudioMode",s.player,generation,AudioManager.MODE_RINGTONE);assertEquals(1f,s.volume,0f);unchanged(s);
  }
  @Test public void releasedOwnerRevokesModeListenerAndCannotResume()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();long generation=(Long)get(a,"mCobraAudioFocusGeneration");AudioManager.OnAudioFocusChangeListener old=listener();assertNotNull(get(a,"mCobraAudioModeListener"));
    call("cobraReleaseAudioFocus",s.player);s.volume=0f;old.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);call("cobraHandleAudioMode",s.player,generation,AudioManager.MODE_NORMAL);
    assertNull(get(a,"mCobraAudioModeListener"));assertEquals(0f,s.volume,0f);
  }
  @Test public void newChannelDoesNotInheritOtherPlayersManualCallPermission()throws Exception{
    manual();Cobra2103202LifecycleTest.State first=playing();interrupt();call("cobraUserPlay",first.player);Cobra2103202LifecycleTest.State next=f.single();call("cobraClaimAudioFocus",next.player);
    assertEquals(0f,next.volume,0f);assertEquals(false,get(a,"mCobraManualCallResume"));assertSame(next.player,get(a,"mCobraAudioFocusPlayer"));
  }
  @Test public void miniPreviewOneTapUsesSameAudioPolicy()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();put(a,"mPlayer",null);put(a,"mCobraPreviewPlayer",s.player);put(a,"mCobraPreviewMuted",false);interrupt();call("toggleCobraPreviewPlayPause");
    assertEquals(1f,s.volume,0f);assertSame(s.player,get(a,"mCobraPreviewPlayer"));assertEquals(0,s.releases);assertEquals(0,s.prepares);
  }
  @Test public void nonSelectedMultiTileCannotClaimOrInheritCallAudio()throws Exception{
    manual();f.multi(3);interrupt();Object r=request();call("cobraUserPlay",f.states.get(0).player);assertSame(r,request());assertEquals(0f,f.states.get(0).volume,0f);
    call("cobraUserPlay",f.states.get(1).player);assertEquals(1f,f.states.get(1).volume,0f);assertEquals(3,((Object[])get(a,"mMultiPlayers")).length);
  }
  @Test public void pipShowsPlayAndActualCallbackResumesTheExistingOwner()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();f.resumePolicy();put(a,"mInPictureInPicture",true);CobraNavigationUiTest.call(get(a,"mCobraPlaybackPolicy"),"pipChanged",true);call("cobraUpdatePipMediaSession");
    MediaSession session=(MediaSession)get(a,"mCobraPipMediaSession");interrupt();assertSame(session,get(a,"mCobraPipMediaSession"));assertEquals(PlaybackState.STATE_PAUSED,((PlaybackState)call("cobraPipPlaybackState",s.player)).getState());
    MediaSession.Callback callback=(MediaSession.Callback)get(get(session,"mCallback"),"mCallback");callback.onPlay();assertEquals(1f,s.volume,0f);assertSame(session,get(a,"mCobraPipMediaSession"));unchanged(s);
  }
  @Test public void backgroundNotificationPlayResumesWithoutReplacingOwner()throws Exception{
    Shadows.shadowOf(RuntimeEnvironment.getApplication()).grantPermissions("android.permission.POST_NOTIFICATIONS");manual();Cobra2103202LifecycleTest.State s=playing();f.save(0,"background","on");assertEquals(true,call("cobraStartOwnedMiniPlayback"));put(a,"mBackgroundStopped",true);
    InfinityExtendedBackgroundService.MiniPlaybackOwner owner=(InfinityExtendedBackgroundService.MiniPlaybackOwner)get(a,"mCobraMiniOwner");interrupt();assertEquals(PlaybackState.STATE_PAUSED,owner.state());owner.command(InfinityExtendedBackgroundService.COMMAND_PLAY);
    assertEquals(1f,s.volume,0f);assertSame(owner,get(a,"mCobraMiniOwner"));owner.command(InfinityExtendedBackgroundService.COMMAND_PAUSE);mode(AudioManager.MODE_NORMAL);assertFalse(s.requested);unchanged(s);
  }
  @Test public void sessionCardReportsPolicyAndGrantWithoutClaimingAudibility()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_FAILED);call("cobraUserPlay",s.player);
    JSONObject card=(JSONObject)call("cobraPlaybackSessionCardSnapshot");assertEquals("denied",card.getString("manual_call_attempt"));assertFalse(card.getBoolean("audio_focus_current_grant"));assertTrue(card.getBoolean("audio_focus_app_muted"));assertEquals("not_observable_by_app",card.getString("call_time_audibility"));
  }
  @Test public void repeatedCallCyclesKeepOnePlayerAndRevokeManualIntentEveryTime()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();for(int i=0;i<8;i++){interrupt();assertEquals(0f,s.volume,0f);call("cobraUserPlay",s.player);assertEquals(1f,s.volume,0f);mode(AudioManager.MODE_NORMAL);unchanged(s);}
  }
  @Test public void rewoundPositionCannotBeResetByCallPlayPauseOrCallEnd()throws Exception{
    manual();final long[] position={42000L};final int[] transportMutations={0};
    Cobra2103202LifecycleTest.State s=f.new State(){
      @Override public Object invoke(Object p,java.lang.reflect.Method m,Object[] values){
        String n=m.getName();if(n.equals("getCurrentPosition")||n.equals("getContentPosition"))return position[0];
        if(n.startsWith("seek")||n.equals("setMediaItem")||n.equals("setMediaSource")||n.equals("stop")){transportMutations[0]++;position[0]=0;}
        return super.invoke(p,m,values);
      }
    };
    f.states.add(s);put(a,"mPlayer",s.player);put(a,"mPlaying",f.channels.get(0));call("openPlayerOverlay",f.channels.get(0));
    f.bind(s,f.channels.get(0),(android.view.TextureView)get(a,"mPlayerTexture"));put(a,"mCobraTimeshiftPlayer",s.player);call("cobraUserPlay",s.player);
    interrupt();call("toggleCobraPlayerPlayPause");call("toggleCobraPlayerPlayPause");assertFalse(s.requested);
    mode(AudioManager.MODE_NORMAL);listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);
    assertEquals(42000L,s.player.getCurrentPosition());assertEquals(0,transportMutations[0]);assertFalse(s.requested);assertSame(s.player,get(a,"mCobraTimeshiftPlayer"));unchanged(s);
  }
  @Test @Config(sdk=25) @GraphicsMode(GraphicsMode.Mode.LEGACY)
  public void legacyFocusPathStillHonorsOptInWithoutApi31Listener()throws Exception{
    manual();Cobra2103202LifecycleTest.State s=playing();interrupt();call("cobraUserPlay",s.player);assertEquals(1f,s.volume,0f);assertNull(request());assertNull(get(a,"mCobraAudioModeListener"));unchanged(s);
  }
}
