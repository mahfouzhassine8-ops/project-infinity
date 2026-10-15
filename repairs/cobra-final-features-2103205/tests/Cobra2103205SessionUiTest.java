package com.projectinfinity.kodi;

import android.app.Application;
import android.content.*;
import android.view.*;
import android.widget.*;
import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.Method;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import static org.junit.Assert.*;

/** Actual Activity integration with controlled channels/player. Not live decode/device acceptance. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class Cobra2103205SessionUiTest {
  CobraNavigationUiTest ui;InfinityLiveActivity a;SharedPreferences prefs;Object first,second;
  static Object get(Object o,String n)throws Exception{return CobraNavigationUiTest.get(o,n);}
  static void put(Object o,String n,Object v)throws Exception{CobraNavigationUiTest.put(o,n,v);}
  Object call(String n,Object...args)throws Exception{return CobraNavigationUiTest.call(a,n,args);}
  @Before @SuppressWarnings("unchecked") public void before()throws Exception{
    CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer.clients.clear();
    ui=new CobraNavigationUiTest();ui.clock();a=ui.fixture(24);prefs=(SharedPreferences)get(a,"mPrefs");
    ((List<Object>)get(a,"mSources")).add(CobraNavigationUiTest.construct("LiveSource","fixture","m3u","Test source","","","","https://example.invalid/list.m3u",""));
    first=((List<?>)get(a,"mChannels")).get(0);second=((List<?>)get(a,"mChannels")).get(1);call("cobraOpenLiveTv");layout();
  }
  @After public void after()throws Exception{if(a!=null){call("closeCobraActionSheet");call("cobraCloseQuickPeekSession");ui.clean(a);}CobraVisualRenderer.clients.clear();}
  void layout()throws Exception{ui.measure(a,412,915);ui.frames(15);}
  View tag(String value){return a.getWindow().getDecorView().findViewWithTag(value);}
  String profile()throws Exception{return ((InfinityCobraFeatureRuntime)get(a,"mFeatures")).activeProfileId();}
  String snapshotKey()throws Exception{return ((InfinityCobraFeatureRuntime)get(a,"mFeatures")).profileKey(CobraSmartReturn.SNAPSHOT);}
  CobraSmartReturn.Snapshot saved(String destination)throws Exception{CobraSmartReturn.Snapshot s=new CobraSmartReturn.Snapshot();s.profile=profile();s.savedAt=System.currentTimeMillis();s.mode="compact";s.channel=(String)get(second,"id");s.selected=s.channel;s.destination=destination;s.playback="fullscreen";s.requested=false;return s;}
  void offer(CobraSmartReturn.Snapshot s)throws Exception{prefs.edit().putBoolean(CobraSmartReturn.ENABLED,true).putString(snapshotKey(),CobraSmartReturn.encode(s)).commit();call("cobraPrepareSmartReturn");}
  static class CounterPlayer extends Cobra2103201SubtitleTest.PlayerDouble {
    final Map<String,Integer> commands=new HashMap<>();
    CounterPlayer(Context c){super(c);}
    @Override public Object invoke(Object proxy,Method method,Object[] args){String n=method.getName();if(n.equals("play")||n.equals("pause")||n.equals("prepare")||n.equals("release")||n.equals("setMediaItem")||n.equals("setVolume")||n.equals("setVideoTextureView")||n.equals("clearVideoSurface")||n.equals("clearVideoTextureView"))commands.put(n,commands.getOrDefault(n,0)+1);return super.invoke(proxy,method,args);}
  }
  CounterPlayer main()throws Exception{
    CounterPlayer fake=new CounterPlayer(a);Object binding=CobraNavigationUiTest.construct("CobraPlayerBinding",a,fake.player,first);((Map<ExoPlayer,Object>)get(a,"mCobraPlayerBindings")).put(fake.player,binding);
    put(a,"mPlayer",fake.player);put(a,"mPlaying",first);FrameLayout overlay=new FrameLayout(a);((FrameLayout)a.getWindow().getDecorView()).addView(overlay,new FrameLayout.LayoutParams(-1,-1));put(a,"mPlayerOverlay",overlay);TextureView texture=new TextureView(a);overlay.addView(texture,new FrameLayout.LayoutParams(-1,-1));put(a,"mPlayerTexture",texture);call("cobraAttachVideo",fake.player,texture);fake.commands.clear();return fake;
  }
  @Test public void pausedColdRestoreKeepsSelectionModeWithoutStartingAnyPlayer()throws Exception{offer(saved("guide"));assertEquals(true,call("cobraTrySmartReturn"));layout();assertEquals("compact",get(a,"mCobraGuideStyle"));assertSame(second,get(a,"mGuidePreviewChannel"));assertNull(get(a,"mPlayer"));assertNull(get(a,"mCobraPreviewPlayer"));assertEquals(false,get(a,"mCobraPreviewAutoplayAllowed"));assertEquals(false,call("cobraTrySmartReturn"));}
  @Test public void offSkipsStoredStateWithoutDeletingIt()throws Exception{offer(saved("guide"));String previous=prefs.getString(snapshotKey(),"");prefs.edit().putBoolean(CobraSmartReturn.ENABLED,false).commit();assertEquals(false,call("cobraTrySmartReturn"));assertEquals(previous,prefs.getString(snapshotKey(),""));assertNull(get(a,"mPlayer"));}
  @Test public void inputAfterLoadingCancelsColdRestore()throws Exception{offer(saved("guide"));a.onUserInteraction();call("cobraSmartLoading");assertEquals(false,call("cobraTrySmartReturn"));assertNull(get(a,"mPlayer"));}
  @Test public void safeModeBypassesSavedReturnWithoutDeletingConfiguration()throws Exception{offer(saved("guide"));String previous=prefs.getString(snapshotKey(),"");a.setIntent(new Intent().putExtra(CobraPresentationSafety.EXTRA_SAFE,true));assertEquals(false,call("cobraTrySmartReturn"));assertEquals(previous,prefs.getString(snapshotKey(),""));assertNull(get(a,"mPlayer"));}
  @Test public void myListIsNotMisidentifiedAsMoviesAndRestoresCorrectRoute()throws Exception{call("showWatchlist");assertEquals("watchlist",call("cobraSmartDestination"));offer(saved("watchlist"));assertEquals(true,call("cobraTrySmartReturn"));layout();assertEquals("watchlist",call("cobraSmartDestination"));assertEquals("COBRA • MY LIST",((TextView)get(a,"mHeader")).getText().toString());call("showSettings");assertEquals("settings",call("cobraSmartDestination"));}
  @Test public void missingChannelCannotStartASavedStream()throws Exception{CobraSmartReturn.Snapshot s=saved("guide");s.channel="deleted:999";s.selected=s.channel;s.requested=true;offer(s);assertEquals(true,call("cobraTrySmartReturn"));assertNull(get(a,"mPlayer"));assertNull(get(a,"mCobraPreviewPlayer"));}
  @Test public void removedSourceCannotStartCachedChannel()throws Exception{CobraSmartReturn.Snapshot s=saved("guide");s.requested=true;offer(s);((List<?>)get(a,"mSources")).clear();assertEquals(true,call("cobraTrySmartReturn"));assertNull(get(a,"mPlayer"));assertNull(get(a,"mCobraPreviewPlayer"));}
  @Test public void quickRecallShowsEightUniqueAllowedChannelsWithoutChangingHistory()throws Exception{List<String> recents=(List<String>)get(a,"mRecents");recents.clear();for(int i=0;i<20;i++){recents.add("fixture:"+i);recents.add("fixture:"+i);}List<String> prior=new ArrayList<>(recents);call("cobraShowPlaybackRecents");layout();for(int i=0;i<8;i++)assertNotNull(tag("cobra-playback-recent:fixture:"+i));assertNull(tag("cobra-playback-recent:fixture:8"));assertEquals(prior,recents);Cobra2103201MenuPolishTest.capture(a,ui,"cobra205-recall-cover",412,915);}
  @Test public void selectingCurrentRecallDoesNotRetuneOrRestartPlayer()throws Exception{CounterPlayer fake=main();call("cobraRecallTune",first);assertSame(fake.player,get(a,"mPlayer"));assertTrue(fake.commands.isEmpty());}
  @Test public void unknownCapacityPeekPreservesMainSurfaceTimeshiftAndRecentsRepeatedly()throws Exception{
    CounterPlayer fake=main();Object texture=get(a,"mPlayerTexture");Object session=CobraNavigationUiTest.construct("CobraLocalTimeshiftSession",a.getCacheDir(),"https://example.invalid/live.ts",Collections.emptyMap(),180,0);put(a,"mCobraTimeshiftSession",session);
    Object policy=get(a,"mCobraPlaybackPolicy");long epoch=(Long)get(policy,"epoch");Map<String,?> before=new HashMap<>(prefs.getAll());
    for(int i=0;i<30;i++){call("cobraShowQuickPeek",second,texture);assertEquals("quick-peek",get(a,"mCobraSheetKind"));assertNull(get(a,"mCobraQuickPeek"));assertNotNull(tag("cobra-quick-peek-play"));assertNotNull(tag("cobra-quick-peek-actions"));call("closeCobraActionSheet");}
    assertSame(fake.player,get(a,"mPlayer"));assertSame(texture,get(a,"mPlayerTexture"));assertSame(session,get(a,"mCobraTimeshiftSession"));assertEquals(epoch,get(policy,"epoch"));assertTrue(fake.commands.isEmpty());assertEquals(before,prefs.getAll());put(a,"mCobraTimeshiftSession",null);
  }
  @Test public void peekIncludesNowNextAndPreservesAllChannelActions()throws Exception{main();call("cobraShowQuickPeek",second,get(a,"mPlayerTexture"));layout();assertTrue(((TextView)tag("cobra_quick_peek_now")).getText().length()>0);assertTrue(((TextView)tag("cobra_quick_peek_next")).getText().length()>0);Cobra2103201MenuPolishTest.capture(a,ui,"cobra205-quick-peek-capacity-guard",412,915);assertTrue(tag("cobra-quick-peek-actions").performClick());assertEquals("channel",get(a,"mCobraSheetKind"));assertNotNull(tag("cobra-channel-preferences"));assertNull(get(a,"mCobraQuickPeekChannel"));}
  @Test public void activeRecordingBlocksAdditionalPreviewConnection()throws Exception{put(a,"mRecordingSession","controlled-recording");assertEquals(true,call("cobraPeekRecordingActive"));call("cobraShowQuickPeek",second,get(a,"mCobraPreviewTexture"));assertEquals("quick-peek",get(a,"mCobraSheetKind"));assertNull(get(a,"mCobraQuickPeek"));assertEquals(View.GONE,tag("cobra_quick_peek_video").getVisibility());}
  @Test public void profileReloadDismissesPeekAndCancelsPendingReturn()throws Exception{main();call("cobraShowQuickPeek",second,get(a,"mPlayerTexture"));offer(saved("guide"));call("reloadProfileCollections");assertNull(get(a,"mCobraQuickPeekChannel"));assertNull(get(a,"mCobraActionSheet"));assertEquals(false,call("cobraTrySmartReturn"));}
  @Test public void settingsControlPersistsOnOffAndKeepsSnapshot()throws Exception{offer(saved("guide"));String previous=prefs.getString(snapshotKey(),"");call("showSettings");assertNotNull(tag("cobra_smart_return_setting"));call("cobraShowSmartReturnSetting");layout();assertTrue(tag("cobra-smart-return:false").performClick());assertFalse(CobraSmartReturn.enabled(prefs));assertEquals(previous,prefs.getString(snapshotKey(),""));call("cobraShowSmartReturnSetting");layout();assertTrue(tag("cobra-smart-return:true").performClick());assertTrue(CobraSmartReturn.enabled(prefs));}
  @Test public void oldProfilePlayerCannotGrantAutoplayToNewProfileSnapshot()throws Exception{main();prefs.edit().putBoolean(CobraSmartReturn.ENABLED,true).commit();InfinityCobraFeatureRuntime features=(InfinityCobraFeatureRuntime)get(a,"mFeatures");String id=features.createProfile("Temporary test profile","",true);assertFalse(id.isEmpty());assertTrue(features.unlockAndSelectProfile(id,""));call("reloadProfileCollections");call("cobraSaveSmartReturn");CobraSmartReturn.Snapshot s=CobraSmartReturn.read(prefs,snapshotKey(),id,System.currentTimeMillis());assertNotNull(s);assertFalse(s.requested);}
}
