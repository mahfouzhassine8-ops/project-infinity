package com.projectinfinity.kodi;
import android.app.Application;
import android.content.SharedPreferences;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;
import java.util.*;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Activity lifecycle/ownership with controlled starting players. Restored non-owner tiles
 * use the existing Java player factory with empty fixture URLs; no provider/decoder proof. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w800dp-h600dp-land-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103202LifecycleTest {
  CobraNavigationUiTest ui;InfinityLiveActivity a;SharedPreferences prefs;List<?> channels;ArrayList<State> states=new ArrayList<>();
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  Object call(String n,Object...v)throws Exception{return CobraNavigationUiTest.call(a,n,v);}
  class State implements InvocationHandler {
    boolean requested=true;int releases,prepares;float volume=1f;TrackSelectionParameters parameters=new TrackSelectionParameters.Builder(a).build();
    final ExoPlayer player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},this);
    public Object invoke(Object p,Method m,Object[] v){String n=m.getName();
      if(n.equals("hashCode"))return System.identityHashCode(p);if(n.equals("equals"))return p==v[0];if(n.equals("toString"))return "Controlled lifecycle";
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return requested;if(n.equals("pause")){requested=false;return null;}if(n.equals("play")){requested=true;return null;}if(n.equals("setPlayWhenReady")){requested=(Boolean)v[0];return null;}
      if(n.equals("release")){releases++;return null;}if(n.equals("prepare")){prepares++;return null;}
      if(n.equals("getVolume"))return volume;if(n.equals("setVolume")){volume=(Float)v[0];return null;}
      if(n.equals("getTrackSelectionParameters"))return parameters;if(n.equals("setTrackSelectionParameters")){parameters=(TrackSelectionParameters)v[0];return null;}
      if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getCurrentTimeline"))return Timeline.EMPTY;if(n.equals("getPlaybackState"))return Player.STATE_READY;
      if(n.equals("getVideoSize"))return new VideoSize(1920,1080);if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;if(n.equals("getApplicationLooper"))return Looper.getMainLooper();
      Class<?> t=m.getReturnType();if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @Before public void before()throws Exception{CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(8);prefs=(SharedPreferences)get(a,"mPrefs");channels=(List<?>)get(a,"mChannels");}
  @After public void after()throws Exception{if(a!=null){call("cobraEndMiniBackgroundPlayback");call("releaseMulti");call("releaseSinglePlayer");ui.clean(a);}CobraVisualRenderer.clients.clear();}
  Object bind(State s,Object c,TextureView t)throws Exception{Object b=CobraNavigationUiTest.construct("CobraPlayerBinding",a,s.player,c);((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(s.player,b);call("cobraAttachVideo",s.player,t);return b;}
  State single()throws Exception{State s=new State();states.add(s);put(a,"mPlayer",s.player);put(a,"mPlaying",channels.get(0));call("openPlayerOverlay",channels.get(0));bind(s,channels.get(0),(TextureView)get(a,"mPlayerTexture"));ui.measure(a,800,600);return s;}
  void multi(int count)throws Exception{
    FrameLayout overlay=new FrameLayout(a),canvas=new FrameLayout(a);overlay.addView(canvas,new FrameLayout.LayoutParams(-1,-1));((FrameLayout)a.getWindow().getDecorView()).addView(overlay,new FrameLayout.LayoutParams(-1,-1));put(a,"mMultiOverlay",overlay);put(a,"mCobraMultiCanvas",canvas);
    Map<String,Object> entries=(Map<String,Object>)get(get(a,"mCobraTiles"),"entries");
    for(int i=0;i<count;i++){State s=new State();states.add(s);Object c=channels.get(i),tile=CobraNavigationUiTest.construct("CobraVideoTile",a,c);put(tile,"player",s.player);entries.put((String)get(c,"id"),tile);canvas.addView((View)get(tile,"view"),new FrameLayout.LayoutParams(1,1));}
    call("cobraSyncMultiArrays");
    for(int i=0;i<count;i++){Object tile=entries.get(get(channels.get(i),"id"));bind(states.get(i),channels.get(i),(TextureView)get(tile,"texture"));}
    call("setMultiAudio",1);call("cobraLayoutPlayerPanels");ui.measure(a,800,600);call("cobraLayoutMultiTiles");
  }
  void save(int channel,String field,String value)throws Exception{Object c=channels.get(channel);String key=(String)call("cobraPreferenceKey",c);Object p=call("cobraReadPreferences",key);put(p,field,value);assertEquals(true,call("cobraSavePreferences",c,key,p,false));}
  void resumePolicy()throws Exception{Object policy=get(a,"mCobraPlaybackPolicy");CobraNavigationUiTest.call(policy,"resume",false);put(a,"mInPictureInPicture",false);call("resumeCobraAfterBackground");}

  @Test public void channelPipOffActuallyDisablesAutomaticEligibilityAndInheritRestoresIt()throws Exception{single();assertEquals(true,call("cobraWantsFullscreenPip"));save(0,"pip","off");assertEquals(false,call("cobraWantsFullscreenPip"));save(0,"pip","inherit");assertEquals(true,call("cobraWantsFullscreenPip"));}
  @Test public void fullscreenBackgroundIsOptInAndDoesNotChangePipPreference()throws Exception{State s=single();assertNull(call("cobraBackgroundCandidate"));save(0,"background","on");assertSame(s.player,call("cobraBackgroundCandidate"));assertEquals(true,call("cobraWantsFullscreenPip"));save(0,"background","off");assertNull(call("cobraBackgroundCandidate"));}
  @Test public void channelPipControlPersistsAndReturnsToPlaybackMenu()throws Exception{single();call("cobraShowChannelSwitch",channels.get(0),"pip");ui.measure(a,800,600);View off=a.getWindow().getDecorView().findViewWithTag("cobra-channel-pip:off");assertNotNull(off);off.performClick();assertEquals(false,call("cobraWantsFullscreenPip"));assertEquals("channel-playback",get(a,"mCobraSheetKind"));String key=(String)call("cobraPreferenceKey",channels.get(0));assertEquals("off",new JSONObject(prefs.getString(key,"")).getString("pip"));}
  @Test public void rewindRuntimeChangeReconnectsOnceAndPreservesPause()throws Exception{prefs.edit().putBoolean("cobra_live_rewind_enabled",false).commit();State original=single();original.requested=false;save(0,"rewind","on");ExoPlayer replacement=(ExoPlayer)get(a,"mPlayer");assertNotSame(original.player,replacement);assertEquals(1,original.releases);assertFalse(replacement.getPlayWhenReady());prefs.edit().putBoolean("cobra_live_rewind_enabled",true).commit();save(0,"rewind","inherit");assertSame(replacement,get(a,"mPlayer"));assertFalse(replacement.getPlayWhenReady());}
  @Test public void onlySelectedMultiAudioScreenCanOwnBackgroundAudio()throws Exception{multi(3);save(1,"background","on");assertSame(states.get(1).player,call("cobraBackgroundCandidate"));call("setMultiAudio",2);assertNull(call("cobraBackgroundCandidate"));}
  @Test public void backgroundOwnerContinuesWhileOtherMultiPlayersPause()throws Exception{multi(3);save(1,"background","on");put(a,"mCobraMiniBackgroundPlayer",states.get(1).player);put(a,"mCobraMiniBackgroundActive",true);call("pauseCobraForBackground");assertFalse(states.get(0).requested);assertTrue(states.get(1).requested);assertFalse(states.get(2).requested);assertEquals(true,call("cobraPlaybackMayRun",states.get(1).player));assertEquals(false,call("cobraPlaybackMayRun",states.get(0).player));}
  @Test public void pipOwnershipPreventsSimultaneousBackgroundAudioOwnership()throws Exception{State s=single();save(0,"background","on");put(a,"mCobraMiniBackgroundPlayer",s.player);put(a,"mCobraMiniBackgroundActive",true);put(a,"mInPictureInPicture",true);assertEquals(false,call("cobraOwnsMiniSession",s.player));}
  @Test public void channelRewindOverrideBeatsGlobalAndInheritReadsGlobal()throws Exception{
    prefs.edit().putBoolean("cobra_live_rewind_enabled",false).commit();save(0,"rewind","on");assertEquals(true,call("cobraChannelRewindEnabled",channels.get(0)));assertEquals(false,call("cobraChannelRewindEnabled",channels.get(1)));
    prefs.edit().putBoolean("cobra_live_rewind_enabled",true).commit();save(0,"rewind","off");assertEquals(false,call("cobraChannelRewindEnabled",channels.get(0)));assertEquals(true,call("cobraChannelRewindEnabled",channels.get(1)));save(0,"rewind","inherit");assertEquals(true,call("cobraChannelRewindEnabled",channels.get(0)));
  }
  @Test public void malformedNewPreferencesFallBackWithoutErasingOlderFields()throws Exception{
    Object parsed=CobraNavigationUiTest.call(CobraNavigationUiTest.construct("CobraChannelPreferences"),"parse",new JSONObject().put("schema",1).put("aspect",3).put("audio","en").put("pip","bad").put("background","yes").put("rewind","enabled").toString());
    assertEquals(3,get(parsed,"aspect"));assertEquals("en",get(parsed,"audio"));for(String n:new String[]{"pip","background","rewind"})assertEquals("inherit",get(parsed,n));
  }
  @Test public void pipPreparationRetainsLayoutAndReusesOwnerWithoutTimeshiftRetune()throws Exception{multi(3);states.get(2).requested=false;prefs.edit().putBoolean("cobra_live_rewind_enabled",true).commit();call("cobraPrepareMultiForPip");assertNull(get(a,"mMultiOverlay"));assertEquals(3,((List<?>)get(a,"mCobraPipMultiChannels")).size());assertSame(states.get(1).player,get(a,"mPlayer"));assertEquals(0,states.get(1).releases);assertEquals(0,states.get(1).prepares);assertEquals(1,states.get(0).releases);assertEquals(1,states.get(2).releases);}
  @Test public void returningRestoresChannelOrderAudioOwnerAndPausedTile()throws Exception{
    multi(3);states.get(2).requested=false;call("cobraPrepareMultiForPip");resumePolicy();call("cobraRestoreMultiAfterPip");ui.measure(a,800,600);
    Object[] restored=(Object[])get(a,"mMultiChannels");assertEquals(3,restored.length);for(int i=0;i<3;i++)assertEquals(get(channels.get(i),"id"),get(restored[i],"id"));assertEquals(1,get(a,"mAudioTile"));ExoPlayer[] players=(ExoPlayer[])get(a,"mMultiPlayers");assertSame(states.get(1).player,players[1]);assertFalse(players[2].getPlayWhenReady());assertNull(get(a,"mCobraPipMultiChannels"));call("cobraRestoreMultiAfterPip");assertSame(players,get(a,"mMultiPlayers"));
  }
  @Test public void restoreWaitsUntilAppReturnsAndNeverRunsInsidePip()throws Exception{multi(2);call("cobraPrepareMultiForPip");put(a,"mInPictureInPicture",true);CobraNavigationUiTest.call(get(a,"mCobraPlaybackPolicy"),"resume",true);call("cobraRestoreMultiAfterPip");assertNull(get(a,"mMultiOverlay"));assertNotNull(get(a,"mCobraPipMultiChannels"));}
  @Test public void dismissedPipRestoresLayoutButDoesNotResumeHiddenPlayback()throws Exception{multi(2);call("cobraPrepareMultiForPip");call("cobraHaltHiddenPlayback");resumePolicy();call("cobraRestoreMultiAfterPip");ExoPlayer[] players=(ExoPlayer[])get(a,"mMultiPlayers");assertEquals(2,players.length);for(ExoPlayer p:players)assertFalse(p.getPlayWhenReady());}
  @Test public void removedSourceChannelIsNotResurrectedOnPipReturn()throws Exception{multi(3);call("cobraPrepareMultiForPip");((List<?>)channels).remove(2);resumePolicy();call("cobraRestoreMultiAfterPip");assertEquals(2,((Object[])get(a,"mMultiChannels")).length);}
  @Test public void staleSavedLayoutCannotReplaceAnotherForegroundChannel()throws Exception{multi(3);call("cobraPrepareMultiForPip");put(a,"mPlaying",channels.get(5));resumePolicy();call("cobraRestoreMultiAfterPip");assertNull(get(a,"mMultiOverlay"));assertNull(get(a,"mCobraPipMultiChannels"));}
  @Test public void repeatedPipRoundTripsKeepOneBindingPerRestoredScreen()throws Exception{multi(3);for(int turn=0;turn<3;turn++){call("cobraPrepareMultiForPip");assertEquals(1,((Map<?,?>)get(a,"mCobraPlayerBindings")).size());resumePolicy();call("cobraRestoreMultiAfterPip");assertEquals(3,((Map<?,?>)get(a,"mCobraPlayerBindings")).size());assertEquals(1,get(a,"mAudioTile"));}}
  @Test public void restartReplacesOnlyCurrentPlayerAndKeepsSavedPreferences()throws Exception{State state=single();save(0,"audio","en");String key=(String)call("cobraPreferenceKey",channels.get(0));String saved=prefs.getString(key,"");call("cobraRestartLiveChannel",channels.get(0),key);assertEquals(1,state.releases);assertNotSame(state.player,get(a,"mPlayer"));assertNotNull(get(a,"mPlayer"));assertEquals(saved,prefs.getString(key,""));assertEquals(1,((Map<?,?>)get(a,"mCobraPlayerBindings")).size());}
  @Test public void launcherReturnRestoresMultiviewInsteadOfClosingIt()throws Exception{multi(3);call("cobraPrepareMultiForPip");put(a,"mCobraLauncherPipReentry",true);resumePolicy();call("cobraConsumeLauncherPipReturn");assertNotNull(get(a,"mMultiOverlay"));assertEquals(3,((Object[])get(a,"mMultiChannels")).length);assertEquals(false,get(a,"mCobraLauncherPipReentry"));}
}
