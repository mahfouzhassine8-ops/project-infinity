package com.projectinfinity.kodi;

import android.content.*;import android.view.*;import android.widget.*;import android.graphics.*;import android.graphics.drawable.*;import android.os.*;
import androidx.media3.common.*;import androidx.media3.exoplayer.ExoPlayer;
import java.lang.reflect.*;import java.util.*;import java.time.Duration;
import org.junit.*;import org.junit.runner.RunWith;import org.robolectric.*;import org.robolectric.annotation.*;
import static org.junit.Assert.*;import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Real Android production views; controlled player/timeline and sports fixtures, no device decoding claims. */
@RunWith(RobolectricTestRunner.class) @Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class CobraProHandoffTest {
  CobraNavigationUiTest f;InfinityLiveActivity a;SharedPreferences prefs;Stub state;ExoPlayer player;
  @Before public void setup()throws Exception{f=new CobraNavigationUiTest();f.clock();a=f.fixture(8);prefs=(SharedPreferences)get(a,"mPrefs");prefs.edit().putBoolean("cobra_live_rewind_enabled",true).putString("cobra_appearance_mode","dark").commit();put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());put(a,"mCobraEffects",new CobraPresentationEffects(a));state=new Stub();player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},state);}
  @After public void cleanup()throws Exception{f.clean(a);}
  Object channel(int index)throws Exception{return ((List)get(a,"mChannels")).get(index);}
  void pro()throws Exception{prefs.edit().putString("guide_view_mode","focus").commit();put(a,"mCobraGuideStyle","focus");call(a,"cobraShowGuideShell");f.measure(a,412,915);}
  void activeMini(int index)throws Exception{Object c=channel(index);put(a,"mGuidePreviewChannel",c);put(a,"mCobraPreviewPlayer",player);put(a,"mCobraPreviewSessionKey",call(a,"cobraChannelKey",c));put(a,"mCobraPreviewMuted",false);put(a,"mCobraProPlaybackOwned",true);put(a,"mCobraProState",CobraProUi.WATCHING);call(a,"cobraProSelectPlayingSlot",c);call(a,"cobraRefreshProHero");}
  CobraProUi.Hero hero()throws Exception{return (CobraProUi.Hero)get(a,"mCobraProHeroUi");}
  View browser()throws Exception{return (View)get(a,"mCobraGuideBrowser");}
  String text(View v){String s=v instanceof TextView?((TextView)v).getText().toString():"";if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)s+="\n"+text(((ViewGroup)v).getChildAt(i));return s;}
  int pixel(Drawable d){d.setBounds(0,0,100,80);Bitmap b=Bitmap.createBitmap(100,80,Bitmap.Config.ARGB_8888);d.draw(new Canvas(b));int c=b.getPixel(50,40);b.recycle();return c;}
  void capture(String name)throws Exception{f.measure(a,412,915);f.frames(20);f.measure(a,412,915);View view=a.getWindow().getDecorView();java.io.File dir=new java.io.File(System.getProperty("cobra.evidence"));dir.mkdirs();Bitmap bitmap=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(bitmap));try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(dir,name+".png"))){assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,out));}bitmap.recycle();}
  static class EdgeTimeline extends Timeline {
    long edge=118000;
    public int getWindowCount(){return 1;}public int getPeriodCount(){return 1;}
    public Window getWindow(int index,Window w,long projection){w.defaultPositionUs=edge*1000;w.durationUs=120000000;w.isSeekable=true;w.isDynamic=true;w.firstPeriodIndex=0;w.lastPeriodIndex=0;return w;}
    public Period getPeriod(int index,Period p,boolean ids){return p.set("period","period",0,120000000,0);}
    public int getIndexOfPeriod(Object uid){return "period".equals(uid)?0:-1;}public Object getUidOfPeriod(int i){return "period";}
  }
  static class Stub implements InvocationHandler {
    long position=118000;boolean playing=true,seekable=true,released;float volume=1;int seeks,prepares,changes,pauses;Timeline timeline=new EdgeTimeline();
    public Object invoke(Object proxy,Method m,Object[] args){String n=m.getName();if(n.equals("equals"))return proxy==args[0];if(n.equals("hashCode"))return System.identityHashCode(proxy);if(n.equals("toString"))return "ControlledProPlayer";
      if(n.equals("getPlayWhenReady")||n.equals("isPlaying"))return playing;if(n.equals("play")){playing=true;return null;}if(n.equals("pause")){playing=false;pauses++;return null;}if(n.equals("setPlayWhenReady")){playing=(Boolean)args[0];return null;}if(n.equals("getVolume"))return volume;if(n.equals("setVolume")){volume=(Float)args[0];return null;}
      if(n.equals("getCurrentPosition")||n.equals("getContentPosition"))return position;if(n.equals("getDuration"))return 120000L;if(n.equals("getCurrentLiveOffset"))return 120000L-position;if(n.equals("getCurrentTimeline"))return timeline;
      if(n.equals("seekToDefaultPosition")){position=((EdgeTimeline)timeline).edge;seeks++;return null;}if(n.equals("isCurrentMediaItemSeekable"))return seekable;if(n.equals("isCurrentMediaItemLive")||n.equals("isCurrentMediaItemDynamic"))return true;
      if(n.equals("release")){released=true;return null;}if(n.equals("prepare")){prepares++;return null;}if(n.equals("setMediaItem")){changes++;return null;}
      if(n.equals("getPlaybackState"))return Player.STATE_READY;if(n.equals("getVideoSize"))return VideoSize.UNKNOWN;if(n.equals("getCurrentTracks"))return Tracks.EMPTY;if(n.equals("getAudioAttributes"))return AudioAttributes.DEFAULT;if(n.equals("getPlaybackParameters"))return PlaybackParameters.DEFAULT;if(n.equals("getTrackSelectionParameters"))return TrackSelectionParameters.DEFAULT_WITHOUT_CONTEXT;if(n.equals("getApplicationLooper"))return Looper.getMainLooper();if(n.equals("getAvailableCommands"))return Player.Commands.EMPTY;if(n.equals("getCurrentCues"))return androidx.media3.common.text.CueGroup.EMPTY_TIME_ZERO;
      Class t=m.getReturnType();if(t==boolean.class)return false;if(t==long.class)return 0L;if(t==int.class)return 0;if(t==float.class)return 0f;if(t==double.class)return 0d;return null;
    }
  }
  @Test public void rowPlayUsesEmbeddedPlayerInAllProChannelCategories()throws Exception{pro();for(int category:new int[]{0,1,2,3}){((List)get(a,"mRecents")).add("fixture:0");call(a,"cobraProFilter",category);if(category==3)call(a,"selectCobraCategory","Documentaries");activeMini(0);state.playing=false;put(a,"mCobraProPlaybackOwned",false);put(a,"mCobraProState",0);ListView list=(ListView)get(a,"mCobraGuideList");CobraProUi.ChannelRow row=(CobraProUi.ChannelRow)list.getAdapter().getView(0,null,list);assertTrue(row.play.performClick());assertSame(player,get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mPlayerOverlay"));assertTrue(state.playing);assertEquals(CobraProUi.WATCHING,get(a,"mCobraProState"));assertTrue((Boolean)get(a,"mCobraProPlaybackOwned"));}}
  @Test public void focusingAndCarouselSwipesCannotRetuneOrPausePlayingChannel()throws Exception{pro();activeMini(0);Object channel=channel(0),texture=get(a,"mCobraPreviewTexture");int index=(Integer)get(a,"mCobraProHeroIndex");CobraProUi.Hero h=hero();h.onTouchEvent(MotionEvent.obtain(0,0,MotionEvent.ACTION_DOWN,300,100,0));h.onTouchEvent(MotionEvent.obtain(0,100,MotionEvent.ACTION_UP,100,100,0));assertNotEquals(index,get(a,"mCobraProHeroIndex"));assertSame(channel,get(a,"mGuidePreviewChannel"));assertSame(player,get(a,"mCobraPreviewPlayer"));assertSame(texture,get(a,"mCobraPreviewTexture"));assertTrue(state.playing);assertEquals(0,state.pauses);assertEquals(0,state.prepares);assertEquals(0,state.changes);assertFalse(state.released);call(a,"selectGuidePreview",channel(2));assertSame(channel,get(a,"mGuidePreviewChannel"));assertTrue(state.playing);assertTrue(h.browsing);assertEquals(View.VISIBLE,h.preview.getVisibility());}
  @Test public void explicitPreviewStillMutesAndPlaysWithoutFullscreen()throws Exception{pro();activeMini(0);call(a,"cobraProPreview");assertSame(player,get(a,"mCobraPreviewPlayer"));assertEquals(0,state.volume,0);assertTrue(state.playing);assertFalse((Boolean)get(a,"mCobraProPlaybackOwned"));assertEquals(CobraProUi.PREVIEW,get(a,"mCobraProState"));assertNull(get(a,"mPlayerOverlay"));assertEquals(View.VISIBLE,hero().unmute.getVisibility());}
  @Test public void fullscreenRoundTripRetainsSameStreamAndWatchingState()throws Exception{pro();activeMini(0);call(a,"promoteCobraPreviewToFullscreen",channel(0));assertSame(player,get(a,"mPlayer"));assertNotNull(get(a,"mPlayerOverlay"));call(a,"closeFullscreenToCobraView");assertSame(player,get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mPlayerOverlay"));assertTrue(state.playing);assertEquals(1,state.volume,0);assertEquals(0,state.prepares);assertEquals(0,state.changes);assertEquals(CobraProUi.WATCHING,get(a,"mCobraProState"));assertEquals(View.GONE,hero().preview.getVisibility());}
  @Test public void controlsHideAndRevealKeepExactViewportCropAndLayout()throws Exception{
    pro();activeMini(0);CobraProUi.Hero h=hero();h.revealControls();f.measure(a,412,915);
    View[] stable={(View)get(a,"mCobraGuideVideo"),(View)get(a,"mCobraPreviewTexture"),(View)get(a,"mCobraGuideBrowser"),(View)get(a,"mCobraGuideDetails"),h.shade,h.transport};
    int[][] before=new int[stable.length][];for(int i=0;i<stable.length;i++)before[i]=bounds(stable[i]);
    float[] crop=new float[9];((TextureView)get(a,"mCobraPreviewTexture")).getTransform(new Matrix()).getValues(crop);
    h.clearFocus();h.collapseControls();f.measure(a,412,915);assertFalse(h.controlsVisible);
    for(int i=0;i<stable.length;i++)assertArrayEquals("Hidden geometry "+i,before[i],bounds(stable[i]));
    assertEquals(View.GONE,h.player[0].getVisibility());assertEquals(View.GONE,h.preview.getVisibility());capture("controls-hidden-fixed-viewport");
    h.performClick();f.measure(a,412,915);assertTrue(h.controlsVisible);assertEquals(View.VISIBLE,h.player[0].getVisibility());
    for(int i=0;i<stable.length;i++)assertArrayEquals("Revealed geometry "+i,before[i],bounds(stable[i]));
    float[] after=new float[9];((TextureView)get(a,"mCobraPreviewTexture")).getTransform(new Matrix()).getValues(after);assertArrayEquals(crop,after,0f);
    assertSame(player,get(a,"mCobraPreviewPlayer"));assertTrue(state.playing);assertEquals(0,state.pauses);assertEquals(0,state.prepares);capture("controls-revealed-fixed-viewport");
  }
  @Test public void sportsTabClearsNonSportsPlaybackAndNoLiveFrame()throws Exception{
    pro();activeMini(0);call(a,"cobraProFilter",4);f.measure(a,412,915);
    assertTrue((Boolean)call(a,"cobraProSportsHeroActive"));assertTrue((Boolean)get(a,"mCobraProSportsCompact"));
    assertNull(get(a,"mGuidePreviewChannel"));assertNull(get(a,"mCobraPreviewPlayer"));assertTrue(state.released);
    assertFalse((Boolean)get(a,"mCobraProPlaybackOwned"));assertFalse((Boolean)get(a,"mCobraPreviewAutoplayAllowed"));
    assertEquals(View.INVISIBLE,((View)get(a,"mCobraPreviewTexture")).getVisibility());
    assertEquals(View.GONE,hero().sportsHome.getVisibility());assertEquals(View.GONE,hero().sportsScore.getVisibility());
    assertTrue(text(hero().info).contains("No games are live right now."));capture("sports-no-live-cleared-video");
  }
  @Test public void liveGameScoresAndMarksRemainInCardsNotVideoHero()throws Exception{pro();Object game=SportsHubTest.game();put(game,"state","in");((List)get(a,"mCobraSportsGames")).add(game);call(a,"cobraProFilter",4);f.measure(a,412,915);assertTrue(hero().sportsMode);assertEquals(View.GONE,hero().sportsScore.getVisibility());assertEquals(View.GONE,hero().sportsAway.getVisibility());CobraProUi.SportsGame data=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",game);ListView list=(ListView)get(a,"mCobraGuideList");CobraProUi.GameRow row=(CobraProUi.GameRow)list.getAdapter().getView(0,null,list);assertEquals(data.score,row.score.getText().toString());assertEquals(View.VISIBLE,row.away.getVisibility());assertEquals(View.VISIBLE,row.home.getVisibility());}
  @Test public void groupsAndEveryTabSelectionSurviveRefreshAndNeighborFocus()throws Exception{pro();for(int index:new int[]{0,1,2,3,4}){call(a,"cobraProFilter",index);call(a,"cobraRenderGuideBrowser");f.measure(a,412,915);CobraProUi.Filters nav=(CobraProUi.Filters)browser().findViewWithTag("pro_six_action_row");for(int i=0;i<6;i++)assertEquals(i==index,nav.buttons[i].isSelected());if(index==3){nav.buttons[2].requestFocus();Bitmap b=Bitmap.createBitmap(nav.buttons[2].getWidth(),nav.buttons[2].getHeight(),Bitmap.Config.ARGB_8888);nav.buttons[2].draw(new Canvas(b));assertNotEquals(CobraProUi.CYAN,b.getPixel(b.getWidth()/2,b.getHeight()-1));b.recycle();}}}
  @Test public void mobileDrawerHidesOnlyViewDestinationAndRetainsModesOnTv()throws Exception{pro();call(a,"toggleCobraDrawer");View drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNull(f.description(drawer,"View"));assertNull(f.description(drawer,"Sports"));call(a,"closeCobraExperienceDrawer");org.robolectric.shadows.ShadowPackageManager pm=Shadows.shadowOf(a.getPackageManager());pm.setSystemFeature("android.software.leanback",true);call(a,"toggleCobraDrawer");drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNotNull(f.description(drawer,"View"));call(a,"closeCobraExperienceDrawer");for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){put(a,"mCobraGuideStyle",mode);call(a,"cobraShowGuideShell");f.measure(a,412,915);assertNotNull(get(a,"mCobraGuideBrowser"));}}
  @Test public void sportsSettingsPreserveTogglesAndMoveTeamManagement()throws Exception{pro();call(a,"showCobraSportsSettings");String copy=text((View)get(a,"mCobraActionSheet"));assertFalse(copy.contains("My Teams"));for(String label:new String[]{"Enabled leagues","Spoiler Protection","Live score ticker","Sports Multi-View overlay","Sports diagnostics"})assertTrue(label,copy.contains(label));call(a,"closeCobraActionSheet");call(a,"cobraProFilter",4);call(a,"cobraProSportsTab",4);assertNotNull(browser().findViewWithTag("pro_team_league_nfl"));}
  @Test public void ambientCyclesTintInactiveRowsAndKeepVideoAcrossProScreens()throws Exception{pro();Object texture=get(a,"mCobraPreviewTexture");prefs.edit().putString(CobraPresentationEffects.AMBIENT,"subtle").commit();call(a,"cobraRenderGuideBrowser");ListView list=(ListView)get(a,"mCobraGuideList");CobraProUi.ChannelRow row=(CobraProUi.ChannelRow)list.getAdapter().getView(1,null,list);assertTrue(row.getBackground() instanceof CobraVisualRenderer.Glass);assertNotEquals(Color.BLACK,pixel(row.getBackground()));for(String mode:new String[]{"off","subtle","immersive","off"}){prefs.edit().putString(CobraPresentationEffects.AMBIENT,mode).commit();call(a,"cobraRefreshAmbient");row.refreshMaterial();assertEquals(mode.equals("off"),pixel(row.getBackground())==Color.BLACK);assertSame(texture,get(a,"mCobraPreviewTexture"));}prefs.edit().putString(CobraPresentationEffects.AMBIENT,"subtle").commit();call(a,"cobraProFilter",4);call(a,"cobraProSportsTab",4);call(a,"showCobraSportsSettings");assertSame(texture,get(a,"mCobraPreviewTexture"));capture("pro-subtle-sports-settings");}
  @Test public void liveEdgeControlsDisabledThenEnabledAndSeekWithoutRestartAcrossAllModes()throws Exception{Object c=channel(0);put(a,"mPlayer",player);put(a,"mPlaying",c);put(a,"mCobraGoLiveButton",call(a,"cobraIcon","play","Go Live",true,null));SeekBar seek=new SeekBar(a);seek.setMax(1000);put(a,"mCobraTimeshiftSeek",seek);for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){put(a,"mCobraGuideStyle",mode);state.position=118000;call(a,"cobraUpdateLiveRewindControls");assertFalse(((View)get(a,"mCobraGoLiveButton")).isEnabled());state.position=30000;call(a,"cobraUpdateLiveRewindControls");assertTrue(((View)get(a,"mCobraGoLiveButton")).isEnabled());call(a,"cobraGoLive");assertEquals(118000,state.position);assertFalse(((View)get(a,"mCobraGoLiveButton")).isEnabled());assertTrue(seek.getProgress()>980);assertEquals(0,state.prepares);assertEquals(0,state.changes);}assertEquals(5,state.seeks);}
  @Test public void unsupportedAndUnknownTimelineLiveControlsStayUnavailable()throws Exception{put(a,"mPlayer",player);put(a,"mPlaying",channel(0));state.seekable=false;assertEquals(false,call(a,"cobraCanGoLive"));state.seekable=true;state.timeline=Timeline.EMPTY;assertEquals(false,call(a,"cobraCanGoLive"));put(a,"mCobraProviderCatchupActive",true);assertEquals(true,call(a,"cobraCanGoLive"));}
  @Test public void leavingProKeepsNewPlaybackInsteadOfRestoringStalePreview()throws Exception{pro();activeMini(0);put(a,"mCobraProPriorPlaying",false);put(a,"mCobraProPriorMuted",true);call(a,"cobraExitProMode");assertSame(player,get(a,"mCobraPreviewPlayer"));assertTrue(state.playing);assertEquals(1,state.volume,0);assertEquals(0,state.pauses);assertFalse(state.released);}
  @Test public void enteringProKeepsExistingUnmutedMiniSession()throws Exception{put(a,"mCobraPreviewPlayer",player);put(a,"mCobraPreviewSessionKey",call(a,"cobraChannelKey",channel(0)));pro();assertSame(player,get(a,"mCobraPreviewPlayer"));assertTrue(state.playing);assertEquals(1,state.volume,0);assertFalse(state.released);assertEquals(CobraProUi.WATCHING,get(a,"mCobraProState"));}
  @Test public void unknownTimeDoesNotCreateAnIndividualReminder()throws Exception{pro();Object game=SportsHubTest.game();put(game,"state","pre");put(game,"timeConfirmed",false);put(game,"startMs",System.currentTimeMillis()+3600000L);call(a,"cobraSportsToggleGameReminder",game);Object runtime=get(a,"mFeatures");assertNull(call(runtime,"sportsReminder",call(a,"cobraSportsKey",game)));}
  @Test public void unconfirmedUpcomingFeedTimeNeverDisplaysPlaceholderClock()throws Exception{org.json.JSONObject root=new CobraProSeason317Test().schedule();org.json.JSONObject event=root.getJSONArray("events").getJSONObject(0);event.put("timeValid",false);Object game=((List)call(a,"cobraSportsParseScoreboard",call(a,"cobraSportsSpec","nfl"),root)).get(0);assertEquals(false,get(game,"timeConfirmed"));CobraProUi.SportsGame data=(CobraProUi.SportsGame)call(a,"cobraProSportsUiGame",game);assertEquals("Time TBA",data.time);assertFalse(data.date.contains("TBA"));assertTrue(data.meta.contains("Time TBA"));assertFalse(data.meta.contains(":"));}
  @Test public void fullscreenSportsSelectionCreatesSecondTileAndKeepsFirstSession()throws Exception{
    pro();((CobraNavigationUiTest.PendingIo)get(a,"mIo")).tasks.clear();
    put(channel(1),"group","Sports");put(channel(2),"group","Sports");
    assertTrue("Fixture must include several eligible sports feeds",((List)call(a,"cobraSportsChannelSnapshot")).size()>1);
    Object game=SportsHubTest.game();put(game,"away",SportsHubTest.team("wild","nfl|wild","Wild","WLD","1"));put(game,"home",SportsHubTest.team("coast","nfl|coast","Coastlines","CST","2"));((List)get(a,"mCobraSportsGames")).add(game);
    activeMini(0);call(a,"promoteCobraPreviewToFullscreen",channel(0));call(a,"showCobraMultiPicker",false);call(a,"renderCobraMultiPicker","SPORTS");
    View picker=(View)get(a,"mCobraMultiPicker");ListView list=(ListView)picker.findViewWithTag("cobra_multi_picker_list");
    assertTrue("Live sports card must invoke its resolver",list.getAdapter().getView(0,null,list).performClick());
    ((CobraNavigationUiTest.PendingIo)get(a,"mIo")).drain();f.frames(3);
    assertTrue("Ambiguous matchup must ask for a broadcast, current filter="+get(a,"mCobraMultiPickerFilter")+", toast="+org.robolectric.shadows.ShadowToast.getTextOfLatestToast(),((String)get(a,"mCobraMultiPickerFilter")).startsWith("SPORTS_CHANNELS:"));
    list=(ListView)picker.findViewWithTag("cobra_multi_picker_list");Object chosen=list.getAdapter().getItem(0);
    assertTrue("Selected broadcast row must invoke launch",list.getAdapter().getView(0,null,list).performClick());
    assertNull(get(a,"mCobraMultiPicker"));assertNotNull(get(a,"mMultiOverlay"));Object[] channels=(Object[])get(a,"mMultiChannels");assertEquals(2,channels.length);
    Object first=call(get(a,"mCobraTiles"),"get",get(channel(0),"id"));Object second=call(get(a,"mCobraTiles"),"get",get(chosen,"id"));
    assertSame(player,get(first,"player"));assertNotNull("Second screen must own a player",get(second,"player"));assertSame(game,((Map)get(a,"mCobraSportsMultiAssignments")).get(get(chosen,"id")));assertFalse(state.released);
    capture("pro-fullscreen-sports-second-tile");call(a,"closePlayer");
  }
  @Test public void sportsLaunchFailureDoesNotRecordFalseGameAssignment()throws Exception{pro();Object game=SportsHubTest.game();assertEquals(false,call(a,"cobraLaunchMultiSportsChannel",channel(1),game));assertTrue(((Map)get(a,"mCobraSportsMultiAssignments")).isEmpty());assertNull(get(a,"mMultiOverlay"));}
  @Test public void powerIconsAnimateOnlyOnceAndCancelIsRedThenNormal()throws Exception{pro();call(a,"showCobraPowerMenu");View decor=a.getWindow().getDecorView();Button cancel=(Button)decor.findViewWithTag("cobra_power_cancel");assertNotNull(cancel);capture("pro-power-icons");CobraProUi.PowerIcon icon=(CobraProUi.PowerIcon)cancel.getCompoundDrawablesRelative()[0];icon.pressed(true);Bitmap b=Bitmap.createBitmap(28,28,Bitmap.Config.ARGB_8888);icon.setBounds(0,0,28,28);icon.draw(new Canvas(b));assertEquals(0xffff5a67,b.getPixel(14,4));b.recycle();icon.pressed(false);assertFalse(icon.down);assertTrue(cancel.performClick());f.frames(30);assertNull(decor.findViewWithTag("cobra_power_menu"));assertFalse(a.isFinishing());assertNull(get(a,"mPlayer"));}
  @Test public void powerAnimationDetachCancelsPendingAction()throws Exception{pro();Button owner=new Button(a);a.addContentView(owner,new ViewGroup.LayoutParams(100,60));CobraProUi.PowerIcon icon=new CobraProUi.PowerIcon(a,"exit",Color.WHITE);boolean[] ran={false};icon.activate(owner,()->ran[0]=true);assertTrue(icon.busy);((ViewGroup)owner.getParent()).removeView(owner);f.frames(30);assertFalse(ran[0]);assertFalse(icon.busy);}

  int[] bounds(View v){return new int[]{v.getLeft(),v.getTop(),v.getWidth(),v.getHeight()};}
  Object addLiveGameForChannel(int index)throws Exception{
    Object game=SportsHubTest.game();put(game,"state","in");put(game,"id","live-owned");
    put(channel(index),"name","ESPN Sports");put(channel(index),"group","Sports");
    ((List)get(game,"broadcasts")).clear();((List)get(game,"broadcasts")).add("ESPN");
    ((List)get(a,"mCobraSportsGames")).add(game);return game;
  }
  @Test public void onlyHeroSwipeRestoresPreviewAndTapCannotOverrideIt()throws Exception{
    pro();activeMini(0);Object current=channel(0);call(a,"selectGuidePreview",channel(2));
    assertFalse(hero().browsing);assertEquals(View.GONE,hero().preview.getVisibility());assertSame(current,get(a,"mGuidePreviewChannel"));
    call(a,"cobraProSelectPlayingSlot",current);call(a,"cobraProStep",1);
    assertTrue(hero().browsing);assertEquals(View.VISIBLE,hero().preview.getVisibility());
    hero().performClick();call(a,"cobraRefreshProHero");assertEquals(View.VISIBLE,hero().preview.getVisibility());
    assertEquals(0f,((View)get(a,"mCobraPreviewTexture")).getAlpha(),0f);assertSame(player,get(a,"mCobraPreviewPlayer"));assertTrue(state.playing);assertFalse(state.released);assertEquals(0,state.pauses);
    call(a,"cobraProPlayChannel",current);assertFalse(hero().browsing);assertEquals(View.GONE,hero().preview.getVisibility());assertEquals(1f,((View)get(a,"mCobraPreviewTexture")).getAlpha(),0f);
  }
  @Test public void sportsCarouselDoesNotStopUnrelatedStreamButNeverShowsItAsSports()throws Exception{
    pro();activeMini(0);put(a,"mCobraProHeroIndex",((Integer)call(a,"cobraProSportsSlotIndex"))-1);call(a,"cobraProStep",1);
    assertTrue((Boolean)call(a,"cobraProSportsHeroActive"));assertSame(player,get(a,"mCobraPreviewPlayer"));assertFalse(state.released);assertTrue(state.playing);
    assertEquals(0f,((View)get(a,"mCobraPreviewTexture")).getAlpha(),0f);assertEquals(0,state.prepares);assertEquals(0,state.pauses);
    call(a,"cobraProFilter",4);assertNull(get(a,"mCobraPreviewPlayer"));assertTrue(state.released);
  }
  @Test public void confirmedSportsSurvivesEntryAndScoreRefreshButStopsWhenGameEnds()throws Exception{
    pro();Object game=addLiveGameForChannel(0);activeMini(0);call(a,"cobraProFilter",4);
    assertSame(player,get(a,"mCobraPreviewPlayer"));assertFalse(state.released);assertTrue((Boolean)call(a,"cobraProSportsHeroActive"));
    call(a,"cobraProOnSportsDataChanged");assertSame(player,get(a,"mCobraPreviewPlayer"));assertFalse(state.released);
    put(game,"state","post");put(game,"completed",true);call(a,"cobraProOnSportsDataChanged");
    assertNull(get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mGuidePreviewChannel"));assertTrue(state.released);assertTrue(text(hero().info).contains("No games are live right now."));
  }
  @Test public void liveGameElsewhereDoesNotAllowUnrelatedChannelInSports()throws Exception{
    pro();((CobraNavigationUiTest.PendingIo)get(a,"mIo")).tasks.clear();addLiveGameForChannel(1);activeMini(0);call(a,"cobraProFilter",4);assertNull(get(a,"mCobraPreviewPlayer"));assertTrue(state.released);
    ((CobraNavigationUiTest.PendingIo)get(a,"mIo")).drain();call(a,"cobraRefreshProHero");
    assertNull(get(a,"mCobraPreviewPlayer"));assertEquals(0,state.prepares);assertFalse((Boolean)get(a,"mCobraPreviewAutoplayAllowed"));
  }
  @Test public void selectingExpiredGameCannotStartAnOldBroadcast()throws Exception{
    pro();Object game=addLiveGameForChannel(0);put(game,"state","post");call(a,"cobraPlaySportsBroadcast",game,channel(0));
    assertNull(get(a,"mCobraPreviewPlayer"));assertNull(get(a,"mPlayer"));assertTrue(org.robolectric.shadows.ShadowToast.getTextOfLatestToast().contains("not live"));
  }
  @Test public void sportsFullscreenReturnKeepsConfirmedPlayerAndDedicatedHero()throws Exception{
    pro();addLiveGameForChannel(0);activeMini(0);call(a,"cobraProFilter",4);
    call(a,"promoteCobraPreviewToFullscreen",channel(0));call(a,"closeFullscreenToCobraView");
    assertSame(player,get(a,"mCobraPreviewPlayer"));assertTrue(state.playing);assertFalse(state.released);
    assertTrue((Boolean)call(a,"cobraProSportsHeroActive"));assertFalse(hero().browsing);assertEquals(CobraProUi.WATCHING,get(a,"mCobraProState"));
  }
  @Test public void returningUnrelatedFullscreenChannelToSportsClearsIt()throws Exception{
    pro();addLiveGameForChannel(0);activeMini(0);call(a,"cobraProFilter",4);
    call(a,"promoteCobraPreviewToFullscreen",channel(0));put(a,"mPlaying",channel(2));call(a,"closeFullscreenToCobraView");
    assertNull(get(a,"mCobraPreviewPlayer"));assertTrue(state.released);assertTrue((Boolean)call(a,"cobraProSportsHeroActive"));
    assertEquals(View.INVISIBLE,((View)get(a,"mCobraPreviewTexture")).getVisibility());
  }
  @Test public void appearanceAndAmbientMatrixRendersAllFiveModes()throws Exception{
    for(String appearance:new String[]{"light","dark"})for(String mode:new String[]{"mobile","grid","compact","cards","focus"})for(String ambient:new String[]{"off","subtle","immersive"}){
      prefs.edit().putString("cobra_appearance_mode",appearance).putString(CobraPresentationEffects.AMBIENT,ambient).commit();
      put(a,"mCobraGuideStyle",mode);call(a,"cobraShowGuideShell");call(a,"cobraApplyAppearanceSettings");call(a,"cobraRefreshAmbient");f.measure(a,412,915);
      String label=appearance+" "+mode+" "+ambient;assertEquals(label,appearance.equals("light")?"light":"oled",call(a,"cobraEffectiveAppearanceMode"));
      assertEquals(label,appearance,prefs.getString("cobra_appearance_mode",""));assertNotNull(get(a,"mCobraGuideBrowser"));
      int panel=(Integer)call(a,"cobraModeColor","panel"),text=(Integer)call(a,"cobraModeColor","text");
      if(appearance.equals("light")){assertTrue(label+" light panel",Color.red(panel)>120&&Color.green(panel)>120);assertTrue(label+" readable ink",Color.red(text)<150);assertFalse((Boolean)call(a,"cobraProOled"));}
      else if(ambient.equals("off")){assertEquals(label,Color.BLACK,panel);assertTrue(label+" light ink",Color.red(text)>150);}
      if(mode.equals("focus")){assertEquals(appearance.equals("light"),hero().light);assertNotEquals("Light Subtle controls cannot be black",appearance.equals("light")?Color.BLACK:Color.WHITE,pixel(hero().transport.getBackground()));}
      if(ambient.equals("off")||mode.equals("focus"))capture("appearance-"+appearance+"-"+mode+"-"+ambient);
    }
  }
  @Test public void followSystemChoosesLightOrOledWithoutAmbientChangingPreference()throws Exception{
    prefs.edit().putString("cobra_appearance_mode","system").commit();android.content.res.Configuration config=a.getResources().getConfiguration();int original=config.uiMode;
    try{for(String ambient:new String[]{"off","subtle","immersive"}){prefs.edit().putString(CobraPresentationEffects.AMBIENT,ambient).commit();
      config.uiMode=(original&~android.content.res.Configuration.UI_MODE_NIGHT_MASK)|android.content.res.Configuration.UI_MODE_NIGHT_NO;assertEquals("light",call(a,"cobraEffectiveAppearanceMode"));
      config.uiMode=(original&~android.content.res.Configuration.UI_MODE_NIGHT_MASK)|android.content.res.Configuration.UI_MODE_NIGHT_YES;assertEquals("oled",call(a,"cobraEffectiveAppearanceMode"));assertEquals("system",prefs.getString("cobra_appearance_mode",""));
    }}finally{config.uiMode=original;}
  }
  @Test public void appearanceChangesKeepPlayerAndPreviewOverrideUntilSwipe()throws Exception{
    pro();activeMini(0);Object texture=get(a,"mCobraPreviewTexture");
    for(String appearance:new String[]{"light","dark","light"}){prefs.edit().putString("cobra_appearance_mode",appearance).commit();call(a,"cobraApplyAppearanceSettings");f.measure(a,412,915);
      assertSame(player,get(a,"mCobraPreviewPlayer"));assertSame(texture,get(a,"mCobraPreviewTexture"));assertTrue(state.playing);assertFalse(state.released);assertFalse(hero().browsing);assertEquals(View.GONE,hero().preview.getVisibility());assertEquals(appearance.equals("light"),hero().light);
    }
  }

}
