package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import androidx.media3.exoplayer.ExoPlayer;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowAudioManager;
import static org.junit.Assert.*;

/** Real Activity focus ownership with controlled players and Android focus responses.
 * Does not establish actual cellular/Bluetooth mixing or physical decoder behavior. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103203AudioFocusTest {
  Cobra2103202LifecycleTest fixture;InfinityLiveActivity a;ShadowAudioManager audio;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(a,n,v);}
  @Before public void before()throws Exception{
    fixture=new Cobra2103202LifecycleTest();fixture.before();a=fixture.a;
    audio=Shadows.shadowOf((AudioManager)a.getSystemService(Context.AUDIO_SERVICE));
    audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_GRANTED);
  }
  @After public void after()throws Exception{if(fixture!=null)fixture.after();}
  AudioManager.OnAudioFocusChangeListener listener()throws Exception{return (AudioManager.OnAudioFocusChangeListener)get(a,"mCobraAudioFocusListener");}
  Object request()throws Exception{return get(a,"mCobraAudioFocusRequest");}
  Cobra2103202LifecycleTest.State preview(boolean muted)throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();put(a,"mPlayer",null);put(a,"mCobraPreviewPlayer",s.player);put(a,"mCobraPreviewMuted",muted);s.volume=muted?0f:1f;return s;
  }
  @Test public void fullscreenUserPlayRetriesFocusAfterInterruptionLeftZeroVolume()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();s.requested=false;s.volume=0f;
    call("toggleCobraPlayerPlayPause");assertTrue(s.requested);assertEquals(1f,s.volume,0f);assertNotNull(request());
    assertSame(s.player,get(a,"mCobraAudioFocusPlayer"));assertEquals(0,s.prepares);assertEquals(0,s.releases);
  }
  @Test public void previewUserPlayRetriesFocusAfterInterruptionLeftZeroVolume()throws Exception{
    Cobra2103202LifecycleTest.State s=preview(false);s.requested=false;s.volume=0f;
    call("toggleCobraPreviewPlayPause");assertTrue(s.requested);assertEquals(1f,s.volume,0f);assertNotNull(request());
  }
  @Test public void explicitPlayUsesHonestMediaMovieAttributesAndDelayedGain()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();call("cobraUserPlay",s.player);AudioFocusRequest r=(AudioFocusRequest)request();
    assertEquals(AudioManager.AUDIOFOCUS_GAIN,r.getFocusGain());assertTrue(r.acceptsDelayedFocusGain());assertFalse("Keep Android automatic notification ducking",r.willPauseWhenDucked());
    assertEquals(android.media.AudioAttributes.USAGE_MEDIA,r.getAudioAttributes().getUsage());
    assertEquals(android.media.AudioAttributes.CONTENT_TYPE_MOVIE,r.getAudioAttributes().getContentType());
  }
  @Test public void deniedFocusDoesNotForceAudiblePlaybackOrRebuildVideo()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();s.requested=false;audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_FAILED);
    call("cobraUserPlay",s.player);assertTrue(s.requested);assertEquals(0f,s.volume,0f);assertEquals(false,get(a,"mCobraAudioFocusAccepted"));
    assertEquals(AudioManager.AUDIOFOCUS_REQUEST_FAILED,get(a,"mCobraAudioFocusResult"));assertEquals(0,s.prepares);assertEquals(0,s.releases);
  }
  @Test public void deniedRequestCannotBeUnmutedByAnUnacceptedCallback()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_FAILED);call("cobraUserPlay",s.player);
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);
  }
  @Test public void delayedFocusRestoresAudioWithoutRetuningTimeshiftOrReplacingPlayer()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();put(a,"mCobraTimeshiftPlayer",s.player);audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_DELAYED);
    call("cobraUserPlay",s.player);assertTrue(s.requested);assertEquals(0f,s.volume,0f);assertEquals(true,get(a,"mCobraAudioFocusAccepted"));
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(1f,s.volume,0f);assertTrue(s.requested);
    assertSame(s.player,get(a,"mPlayer"));assertSame(s.player,get(a,"mCobraTimeshiftPlayer"));assertEquals(0,s.prepares);assertEquals(0,s.releases);
  }
  @Test public void userPauseBeforeDelayedGainNeverStartsPlayerAgain()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_DELAYED);call("cobraUserPlay",s.player);
    call("toggleCobraPlayerPlayPause");assertFalse(s.requested);listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertFalse(s.requested);
  }
  @Test public void allExistingFocusLossesPreserveVideoAndTimeshiftUntilGain()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();put(a,"mCobraTimeshiftPlayer",s.player);call("cobraUserPlay",s.player);
    for(int loss:new int[]{AudioManager.AUDIOFOCUS_LOSS,AudioManager.AUDIOFOCUS_LOSS_TRANSIENT,AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK}){
      listener().onAudioFocusChange(loss);assertTrue(s.requested);assertEquals(0f,s.volume,0f);assertSame(s.player,get(a,"mCobraTimeshiftPlayer"));
      listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(1f,s.volume,0f);assertEquals(0,s.prepares);assertEquals(0,s.releases);
    }
  }
  @Test public void automaticRecoveryDoesNotStealFocusAfterAnotherAppInterruption()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();call("cobraUserPlay",s.player);Object r=request();
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS);s.requested=false;call("startCobraPlayer",s.player);
    assertSame(r,request());assertTrue(s.requested);assertEquals(0f,s.volume,0f);
  }
  @Test public void staleCallbackCannotMuteOrUnmuteNewRequestForSamePlayer()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();call("cobraUserPlay",s.player);AudioManager.OnAudioFocusChangeListener old=listener();Object oldRequest=request();
    call("cobraUserPlay",s.player);assertNotSame(oldRequest,request());assertSame(oldRequest,audio.getLastAbandonedAudioFocusRequest());
    old.onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS);assertEquals(1f,s.volume,0f);
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);old.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);
  }
  @Test public void releaseAbandonsExactRequestAndRevokesOutstandingCallbacks()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();call("cobraUserPlay",s.player);AudioManager.OnAudioFocusChangeListener old=listener();Object r=request();
    call("cobraReleaseAudioFocus",s.player);s.volume=0f;old.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);
    assertEquals(0f,s.volume,0f);assertNull(get(a,"mCobraAudioFocusPlayer"));assertNull(request());assertSame(r,audio.getLastAbandonedAudioFocusRequest());
  }
  @Test public void releasedOwnersCallbackCannotAlterReplacementOwner()throws Exception{
    Cobra2103202LifecycleTest.State first=fixture.single();call("cobraUserPlay",first.player);AudioManager.OnAudioFocusChangeListener old=listener();
    Cobra2103202LifecycleTest.State replacement=fixture.single();call("cobraUserPlay",replacement.player);listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);
    old.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,replacement.volume,0f);assertSame(replacement.player,get(a,"mCobraAudioFocusPlayer"));
  }
  @Test public void mutedPreviewPlayPreservesMuteAndDoesNotRequestFocus()throws Exception{
    Cobra2103202LifecycleTest.State s=preview(true);s.requested=false;Object last=audio.getLastAudioFocusRequest();
    call("cobraUserPlay",s.player);assertTrue(s.requested);assertEquals(0f,s.volume,0f);assertSame(last,audio.getLastAudioFocusRequest());assertNull(get(a,"mCobraAudioFocusPlayer"));
  }
  @Test public void nonSelectedMultiViewTileNeverClaimsTheAudioOwner()throws Exception{
    fixture.multi(3);Cobra2103202LifecycleTest.State silent=fixture.states.get(0),selected=fixture.states.get(1);silent.requested=false;Object r=request();
    call("cobraUserPlay",silent.player);assertTrue(silent.requested);assertEquals(0f,silent.volume,0f);assertSame(r,request());assertSame(selected.player,get(a,"mCobraAudioFocusPlayer"));
  }
  @Test public void hiddenUnownedUserPlayCannotRestartBackgroundPlayer()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();s.requested=false;put(a,"mBackgroundStopped",true);
    call("cobraUserPlay",s.player);assertFalse(s.requested);assertNull(request());
  }
  @Test public void staleUnknownPlayerPlayCannotAcquireFocus()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.new State();s.requested=false;call("cobraUserPlay",s.player);
    assertFalse(s.requested);assertNull(request());assertNull(get(a,"mCobraAudioFocusPlayer"));
  }
  @Test public void focusGainAfterPipDismissalCannotRestartHiddenPlayback()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_DELAYED);call("cobraUserPlay",s.player);
    AudioManager.OnAudioFocusChangeListener pending=listener();call("cobraHaltHiddenPlayback");assertFalse(s.requested);
    pending.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertFalse(s.requested);assertEquals(0,s.prepares);
  }
  @Test public void backgroundMediaOwnerPlayRetriesFocusFromZeroVolume()throws Exception{
    Shadows.shadowOf(RuntimeEnvironment.getApplication()).grantPermissions("android.permission.POST_NOTIFICATIONS");
    Cobra2103202LifecycleTest.State s=fixture.single();fixture.save(0,"background","on");
    assertEquals(true,call("cobraStartOwnedMiniPlayback"));put(a,"mBackgroundStopped",true);
    InfinityExtendedBackgroundService.MiniPlaybackOwner owner=(InfinityExtendedBackgroundService.MiniPlaybackOwner)get(a,"mCobraMiniOwner");
    assertNotNull(owner);owner.command(InfinityExtendedBackgroundService.COMMAND_PAUSE);assertFalse(s.requested);s.volume=0f;
    owner.command(InfinityExtendedBackgroundService.COMMAND_PLAY);assertTrue(s.requested);assertEquals(1f,s.volume,0f);assertSame(s.player,get(a,"mCobraAudioFocusPlayer"));
    owner.command(InfinityExtendedBackgroundService.COMMAND_PAUSE);listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertFalse(s.requested);
  }
  @Test public void replacingDelayedRequestRevokesItsPendingGain()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();audio.setNextFocusRequestResponse(AudioManager.AUDIOFOCUS_REQUEST_DELAYED);call("cobraUserPlay",s.player);
    AudioManager.OnAudioFocusChangeListener pending=listener();Object old=request();call("cobraUserPlay",s.player);
    assertNotSame(old,request());assertSame(old,audio.getLastAbandonedAudioFocusRequest());pending.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);
    listener().onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(1f,s.volume,0f);
  }
  @Test public void focusCallbackCannotAlterFinishingActivityPlayback()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();call("cobraUserPlay",s.player);AudioManager.OnAudioFocusChangeListener pending=listener();s.volume=0f;a.finish();
    pending.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);
  }
  @Test @Config(sdk=25) @GraphicsMode(GraphicsMode.Mode.LEGACY)
  public void legacyAndroidUsesMusicFocusAndAbandonsSameListener()throws Exception{
    Cobra2103202LifecycleTest.State s=fixture.single();s.volume=0f;call("cobraUserPlay",s.player);
    ShadowAudioManager.AudioFocusRequest last=audio.getLastAudioFocusRequest();assertNotNull(last);assertNull(request());
    assertEquals(AudioManager.STREAM_MUSIC,last.streamType);assertEquals(AudioManager.AUDIOFOCUS_GAIN,last.durationHint);assertSame(listener(),last.listener);assertEquals(1f,s.volume,0f);
    last.listener.onAudioFocusChange(AudioManager.AUDIOFOCUS_LOSS_TRANSIENT);assertEquals(0f,s.volume,0f);assertTrue(s.requested);
    call("cobraReleaseAudioFocus",s.player);assertSame(last.listener,audio.getLastAbandonedAudioFocusListener());last.listener.onAudioFocusChange(AudioManager.AUDIOFOCUS_GAIN);assertEquals(0f,s.volume,0f);
  }
}
