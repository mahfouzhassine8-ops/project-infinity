package com.projectinfinity.kodi;

import android.app.Activity;
import android.app.Application;
import android.app.PictureInPictureParams;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import androidx.media3.exoplayer.DefaultLoadControl;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import java.io.File;
import java.io.FileOutputStream;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.Shadows;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.Implementation;
import org.robolectric.annotation.Implements;
import org.robolectric.annotation.LooperMode;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowActivity;
import static org.junit.Assert.*;
import static com.projectinfinity.kodi.CobraNavigationUiTest.*;

/** Actual production layouts/listeners. Only decoder creation, PiP platform and TS I/O are controlled. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi",
    instrumentedPackages={"com.projectinfinity.kodi"},
    shadows={CobraCleanRuntimeTest.PlayerFactory.class,CobraCleanRuntimeTest.PipPlatform.class,CobraCleanRuntimeTest.TsIo.class})
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraCleanRuntimeTest {
  static final String[] MODES={"mobile","compact","cards","grid","focus","sports"};
  static final int[][] SIZES={{412,915},{915,412},{720,840},{840,720},{280,280}};
  static final ArrayList<Playback> created=new ArrayList<>();
  static class Playback extends CobraProHandoffTest.Stub {
    ExoPlayer proxy;float preparedVolume=Float.NaN,startedVolume=Float.NaN;
    Playback(){proxy=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class[]{ExoPlayer.class},this);}
    @Override public Object invoke(Object p,Method method,Object[] args){
      if(method.getName().equals("prepare"))preparedVolume=volume;
      if(method.getName().equals("play") || (method.getName().equals("setPlayWhenReady") && Boolean.TRUE.equals(args[0])))startedVolume=volume;
      return super.invoke(p,method,args);
    }
  }
  @Implements(value=CobraQuickPeekSession.class,isInAndroidSdk=false)
  public static class PlayerFactory {
    @Implementation protected static ExoPlayer createPlayer(Context c,DefaultMediaSourceFactory f,DefaultLoadControl l){Playback p=new Playback();created.add(p);return p.proxy;}
  }
  @Implements(Activity.class)
  public static class PipPlatform extends ShadowActivity {
    static boolean permitted=true,inPip;static int requests;
    @Implementation protected boolean enterPictureInPictureMode(PictureInPictureParams params){assertNotNull(params);requests++;return permitted;}
    @Implementation protected boolean isInPictureInPictureMode(){return inPip;}
  }
  @Implements(className="com.projectinfinity.kodi.InfinityLiveActivity$CobraLocalTimeshiftSession",isInAndroidSdk=false)
  public static class TsIo {
    static int starts;
    @Implementation protected void start(){starts++;}
    @Implementation protected String liveUrl(){return "http://127.0.0.1:9/controlled-live.ts";}
    @Implementation protected void stop(){}
  }
  CobraNavigationUiTest f;InfinityLiveActivity a;SharedPreferences prefs;Playback state;Object game;
  int width=412,height=915;
  @Before public void before(){f=new CobraNavigationUiTest();f.clock();created.clear();PipPlatform.permitted=true;PipPlatform.inPip=false;PipPlatform.requests=0;TsIo.starts=0;}
  @After public void after()throws Exception{close();}
  void close()throws Exception{if(a!=null){call(a,"closeCobraActionSheet");call(a,"closeCobraPlayerDrawer");call(a,"closePlayer");call(a,"stopCobraPreview");f.clean(a);a=null;}PipPlatform.inPip=false;}
  void window(int w,int h)throws Exception{
    width=w;height=h;RuntimeEnvironment.setQualifiers("w"+w+"dp-h"+h+"dp-"+(w>h?"land":"port")+"-mdpi");
    if(a==null)return;
    Shadows.shadowOf(a.getWindowManager().getDefaultDisplay()).setWidth(w);Shadows.shadowOf(a.getWindowManager().getDefaultDisplay()).setHeight(h);
    WindowManager.LayoutParams lp=a.getWindow().getAttributes();lp.width=w;lp.height=h;a.getWindow().setAttributes(lp);measure();
  }
  void measure()throws Exception{f.measure(a,width,height);assertEquals(width,a.getWindow().getDecorView().getWidth());assertEquals(height,a.getWindow().getDecorView().getHeight());}
  @SuppressWarnings("unchecked") void open(String mode,boolean muted)throws Exception{
    close();a=f.fixture(8);prefs=(SharedPreferences)get(a,"mPrefs");
    prefs.edit().putString("guide_view_mode",mode.equals("sports")?"focus":mode).putString("cobra_appearance_mode","dark").putBoolean("cobra_live_rewind_enabled",false).commit();
    List<Object> channels=(List<Object>)get(a,"mChannels");channels.clear();
    for(int i=0;i<8;i++)channels.add(construct("Channel","fixture:"+i,"Channel "+i,i%2==0?"Documentaries":"Entertainment","ch"+i,"","http://127.0.0.1:9/"+i+".m3u8","",Collections.emptyMap()));
    ((Set<String>)get(a,"mFavorites")).addAll(Arrays.asList("fixture:0","fixture:2","fixture:4"));
    ((List<String>)get(a,"mRecents")).clear();((List<String>)get(a,"mRecents")).addAll(Arrays.asList("fixture:0","fixture:2","fixture:4"));
    put(a,"mGuidePreviewChannel",channels.get(0));put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());
    put(a,"mCobraGuideStyle",mode.equals("sports")?"focus":mode);call(a,"cobraShowGuideShell");window(width,height);
    game=SportsHubTest.game();put(game,"venue","Ford Field");put(game,"timeConfirmed",true);
    if(mode.equals("sports")){((List)get(a,"mCobraSportsGames")).add(game);call(a,"cobraProFilter",4);}
    state=new Playback();state.volume=muted?0:1;
    Object ch=channel(0);put(a,"mGuidePreviewChannel",ch);put(a,"mCobraPreviewPlayer",state.proxy);put(a,"mCobraPreviewSessionKey",call(a,"cobraChannelKey",ch));put(a,"mCobraPreviewMuted",muted);
    InfinityLiveActivity.CobraMediaAudioState audio=(InfinityLiveActivity.CobraMediaAudioState)call(a,"cobraMediaAudioState",state.proxy);if(muted)audio.mute();else audio.unmute();
    if(mode.equals("focus") || mode.equals("sports")){
      put(a,"mCobraProPlaybackOwned",true);put(a,"mCobraProState",CobraProUi.WATCHING);
      if(mode.equals("sports")){
        put(a,"mCobraProSportsPlaybackGameId",get(game,"id"));put(a,"mCobraProSportsPlaybackChannelKey",call(a,"cobraChannelKey",ch));put(a,"mCobraProSportsGameId",get(game,"id"));
        put(a,"mCobraProHeroIndex",call(a,"cobraProSportsSlotIndex"));put(a,"mCobraProSportsResolvedChannel",ch);
      }else call(a,"cobraProSelectPlayingSlot",ch);
      call(a,"cobraRefreshProHero");call(a,"cobraSetProState",CobraProUi.WATCHING,false);
    }
    measure();
  }
  Object channel(int i)throws Exception{return ((List)get(a,"mChannels")).get(i);}
  View decor(){return a.getWindow().getDecorView();}
  View tag(String value){return decor().findViewWithTag(value);}
  void full()throws Exception{call(a,"promoteCobraPreviewToFullscreen",get(a,"mGuidePreviewChannel"));measure();assertSame(state.proxy,get(a,"mPlayer"));assertNotNull(get(a,"mPlayerOverlay"));}
  View description(View root,String value){return f.description(root,value);}
  void click(View v)throws Exception{assertNotNull("Required production control",v);assertTrue("Attached control",v.isAttachedToWindow());assertTrue("Shown control "+v.getContentDescription(),v.isShown());assertTrue(v.performClick());measure();}
  Rect rect(View v){Rect r=new Rect();assertTrue(v.getGlobalVisibleRect(r));return r;}
  String text(View v){String s=v instanceof TextView?((TextView)v).getText().toString():"";if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)s+="\n"+text(((ViewGroup)v).getChildAt(i));return s;}
  View clickableText(View v,String exact){if(v instanceof TextView&&exact.equals(((TextView)v).getText().toString())&&v.isClickable())return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View found=clickableText(((ViewGroup)v).getChildAt(i),exact);if(found!=null)return found;}return null;}
  View button(View v){if(v instanceof Button)return v;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++){View found=button(((ViewGroup)v).getChildAt(i));if(found!=null)return found;}return null;}
  void listIndex(ListView list,int position)throws Exception{list.setSelection(position);measure();assertTrue(position>=list.getFirstVisiblePosition()&&position<=list.getLastVisiblePosition());}
  void evidence(String name,JSONObject json)throws Exception{
    File dir=new File(System.getProperty("cobra.clean.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());
    Files.write(new File(dir,name+".json").toPath(),json.toString(2).getBytes(StandardCharsets.UTF_8));
  }
  void screenshot(String name)throws Exception{File dir=new File(System.getProperty("cobra.clean.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());Bitmap b=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);decor().draw(new Canvas(b));try(FileOutputStream stream=new FileOutputStream(new File(dir,name+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,stream));}finally{b.recycle();}}
  List<String> controls()throws Exception{LinearLayout tools=(LinearLayout)tag("cobra_fullscreen_controls");assertNotNull(tools);List<String> result=new ArrayList<>();for(int i=0;i<tools.getChildCount();i++)result.add(String.valueOf(tools.getChildAt(i).getContentDescription()));return result;}
  void checkControls(String mode)throws Exception{
    boolean pro=mode.equals("focus")||mode.equals("sports"),sports=mode.equals("sports");
    assertEquals(sports?Arrays.asList("Channels","Display","Multi-View","PiP","Stats","More"):Arrays.asList("Channels","Display","Multi-View","PiP","More"),controls());
    assertEquals(pro,tag("cobra_pro_fullscreen_scroll")!=null);assertEquals(sports,tag("cobra_fullscreen_sports_stats")!=null);
    assertNull(description((View)get(a,"mPlayerChrome"),"Status"));
  }
  @Test public void allSixAttachedControlInventoriesFollowActualModeNotSavedPreference()throws Exception{
    JSONArray inventory=new JSONArray();
    for(String mode:MODES){open(mode,false);prefs.edit().putString("guide_view_mode","focus").commit();full();checkControls(mode);
      inventory.put(new JSONObject().put("mode",mode).put("controls",new JSONArray(controls())).put("proScroll",tag("cobra_pro_fullscreen_scroll")!=null));}
    evidence("SIX-MODE-INVENTORY",new JSONObject().put("contexts",inventory));
  }
  @Test public void modeSwitchDropsOldProControlsAndSportsStatistics()throws Exception{
    open("sports",false);full();checkControls("sports");
    for(String mode:new String[]{"compact","cards","grid","mobile","focus"}){call(a,"cobraSwitchMode",mode);measure();checkControls(mode);assertNull(tag("cobra_pro_stats_panel"));}
  }
  @Test public void proScrollIsTouchScrollableAndHasNoDirectionIndicators()throws Exception{
    window(280,280);open("sports",false);full();android.widget.HorizontalScrollView scroll=(android.widget.HorizontalScrollView)tag("cobra_pro_fullscreen_scroll");
    assertFalse(scroll.isHorizontalScrollBarEnabled());assertTrue(scroll.getChildAt(0).getWidth()>scroll.getWidth());scroll.scrollTo(10000,0);measure();assertTrue(scroll.getScrollX()>0);
    assertFalse(text(scroll).contains("Swipe"));assertNull(description(scroll,"Scroll left"));assertNull(description(scroll,"Scroll right"));
  }
  @Test public void mutedPreviewPipNeverIntersectsAnyOriginalHeroTargetAtFiveActualSizes()throws Exception{
    for(int[] size:SIZES){window(size[0],size[1]);open("focus",true);put(a,"mCobraProPlaybackOwned",false);call(a,"cobraSetProState",CobraProUi.PREVIEW,false);measure();
      CobraProUi.Hero hero=(CobraProUi.Hero)get(a,"mCobraProHeroUi");View pip=tag("cobra_pro_preview_pip");assertNotNull(pip);assertTrue(pip.isShown());assertTrue(pip.getWidth()>=40&&pip.getHeight()>=40);
      Rect p=rect(pip);JSONArray old=new JSONArray();
      for(View v:new View[]{hero.unmute,hero.left,hero.right,hero.status,hero.preview,hero.sportsStats,hero.sportsWatch,hero.sportsMulti})if(v.getVisibility()==View.VISIBLE&&v.getAlpha()>0&&v.getGlobalVisibleRect(new Rect())){
        Rect r=rect(v);assertFalse("New PiP overlap: "+v.getContentDescription()+" at "+size[0]+"x"+size[1],Rect.intersects(p,r));old.put(new JSONObject().put("name",String.valueOf(v.getContentDescription())).put("rect",new JSONArray(new int[]{r.left,r.top,r.right,r.bottom})));}
      evidence("PIP-GEOMETRY-"+size[0]+"x"+size[1],new JSONObject().put("width",width).put("height",height).put("pip",new JSONArray(new int[]{p.left,p.top,p.right,p.bottom})).put("originalTargets",old));screenshot("pip-preview-"+width+"x"+height);
    }
  }
  void pipCycle()throws Exception{
    assertEquals(1,PipPlatform.requests);PipPlatform.inPip=true;a.onPictureInPictureModeChanged(true,a.getResources().getConfiguration());
    PipPlatform.inPip=false;put(get(a,"mCobraPlaybackPolicy"),"resumed",true);a.onPictureInPictureModeChanged(false,a.getResources().getConfiguration());f.frames(2);measure();
  }
  View miniPip()throws Exception{
    if((Boolean)get(a,"mCobraProActive")){CobraProUi.Hero h=(CobraProUi.Hero)get(a,"mCobraProHeroUi");h.revealControls();measure();return h.player[8];}
    return tag("cobra_preview_pip");
  }
  @Test public void miniPipReturnsEveryOriginWithSamePlayerAndBothMuteStates()throws Exception{
    for(String mode:MODES)for(boolean muted:new boolean[]{false,true}){
      open(mode,muted);PipPlatform.requests=0;Object origin=get(a,"mCobraGuideStyle");click(miniPip());assertSame(state.proxy,get(a,"mPlayer"));pipCycle();
      assertNull("Mini PiP must return to mini: "+mode,get(a,"mPlayerOverlay"));assertSame(state.proxy,get(a,"mCobraPreviewPlayer"));assertEquals(origin,get(a,"mCobraGuideStyle"));assertEquals(muted,((InfinityLiveActivity.CobraMediaAudioState)call(a,"cobraMediaAudioState",state.proxy)).userMuted);assertEquals(muted?0:1,state.volume,0);assertEquals(0,state.prepares);assertFalse(state.released);
    }
  }
  @Test public void fullscreenPipKeepsFullscreenOriginAndSameSession()throws Exception{
    for(String mode:MODES)for(boolean muted:new boolean[]{false,true}){open(mode,muted);full();Object overlay=get(a,"mPlayerOverlay");PipPlatform.requests=0;click(tag("cobra_fullscreen_pip"));pipCycle();assertSame(overlay,get(a,"mPlayerOverlay"));assertSame(state.proxy,get(a,"mPlayer"));checkControls(mode);assertEquals(muted,((InfinityLiveActivity.CobraMediaAudioState)call(a,"cobraMediaAudioState",state.proxy)).userMuted);assertEquals(0,state.prepares);}
  }
  @Test public void deniedMiniPipDoesNotLoseTheOriginatingPlayer()throws Exception{
    open("focus",false);PipPlatform.permitted=false;click(miniPip());assertEquals(1,PipPlatform.requests);assertNull(get(a,"mPlayerOverlay"));assertSame(state.proxy,get(a,"mCobraPreviewPlayer"));assertEquals("focus",get(a,"mCobraGuideStyle"));assertFalse(state.released);
  }
  void channels(String category)throws Exception{
    click(description((View)get(a,"mPlayerChrome"),"Channels"));click(tag("cobra_player_tab_"+category));
    if(category.equals("CATEGORIES")){ListView list=(ListView)get(a,"mCobraPlayerDrawerList");int group=-1;for(int i=0;i<list.getCount();i++)if("Documentaries".equals(list.getItemAtPosition(i)))group=i;assertTrue(group>=0);listIndex(list,group);click(button(list.getChildAt(group-list.getFirstVisiblePosition())));assertEquals("GROUP:Documentaries",get(a,"mCobraDrawerFilter"));}
  }
  void chooseDifferent()throws Exception{
    ListView list=(ListView)get(a,"mCobraPlayerDrawerList");Object playing=get(a,"mPlaying");int target=-1;for(int i=0;i<list.getCount();i++)if(list.getItemAtPosition(i)!=playing){target=i;break;}assertTrue("Fixture must expose a genuinely different channel",target>=0);
    Object expected=list.getItemAtPosition(target);ExoPlayer old=(ExoPlayer)get(a,"mPlayer");listIndex(list,target);click(button(list.getChildAt(target-list.getFirstVisiblePosition())));assertSame(expected,get(a,"mPlaying"));assertNotSame("Must actually replace player",old,get(a,"mPlayer"));assertFalse(created.isEmpty());assertSame(created.get(created.size()-1).proxy,get(a,"mPlayer"));
  }
  @Test public void realChannelsAllFavoritesRecentAndGroupsKeepUserMuteInEveryMode()throws Exception{
    JSONArray cases=new JSONArray();for(String mode:MODES)for(boolean muted:new boolean[]{false,true})for(String category:new String[]{"ALL","FAVORITES","RECENT","CATEGORIES"}){
      open(mode,muted);full();channels(category);chooseDifferent();Playback next=created.get(created.size()-1);
      assertEquals(muted,((InfinityLiveActivity.CobraMediaAudioState)call(a,"cobraMediaAudioState",next.proxy)).userMuted);assertEquals(muted?0:1,next.preparedVolume,0);assertEquals(muted?0:1,next.startedVolume,0);
      cases.put(new JSONObject().put("mode",mode).put("muted",muted).put("category",category).put("preparedVolume",next.preparedVolume));
    }evidence("CHANNELS-AUDIO-MATRIX",new JSONObject().put("cases",cases));
  }
  @Test public void temporarySilenceIsNotMisclassifiedAsUserMute()throws Exception{
    open("mobile",false);full();state.volume=0;channels("ALL");chooseDifferent();Playback next=created.get(created.size()-1);assertFalse(((InfinityLiveActivity.CobraMediaAudioState)call(a,"cobraMediaAudioState",next.proxy)).userMuted);assertEquals(1,next.preparedVolume,0);
  }
  @Test public void directTuningOutsideChannelsDoesNotInheritNewMuteBehavior()throws Exception{
    open("focus",true);full();put(a,"mPlaying",channel(2));call(a,"startSinglePlayer",get(channel(2),"primaryUrl"));assertFalse(created.isEmpty());Playback next=created.get(created.size()-1);assertFalse(((InfinityLiveActivity.CobraMediaAudioState)call(a,"cobraMediaAudioState",next.proxy)).userMuted);assertEquals(1,next.preparedVolume,0);
  }
  @Test public void actualLocalRewindProxyReceivesMuteBeforePrepare()throws Exception{
    for(boolean muted:new boolean[]{true,false}){
      open("focus",muted);Object old=channel(2);Object ts=construct("Channel",get(old,"id"),get(old,"name"),get(old,"group"),get(old,"epgId"),"","http://127.0.0.1:9/channel.ts","",Collections.emptyMap());((List)get(a,"mChannels")).set(2,ts);prefs.edit().putBoolean("cobra_live_rewind_enabled",true).commit();
      full();channels("FAVORITES");chooseDifferent();assertTrue(TsIo.starts>0);assertSame(get(a,"mPlayer"),get(a,"mCobraTimeshiftProxyPlayer"));Playback next=created.get(created.size()-1);assertEquals(muted?0:1,next.preparedVolume,0);assertEquals(muted?0:1,next.startedVolume,0);
    }
  }
  @SuppressWarnings("unchecked") void broadcasts(int count)throws Exception{
    List<Object> channels=(List<Object>)get(a,"mChannels");for(int i=0;i<count;i++)channels.add(construct("Channel","broadcast:"+i,"ESPN2 Broadcast "+i,"Sports","espn"+i,"","http://127.0.0.1:9/broadcast"+i+".m3u8","",Collections.emptyMap()));
    if(((List)get(a,"mCobraSportsGames")).isEmpty())((List)get(a,"mCobraSportsGames")).add(game);
    put(a,"mCobraSportsLastRefresh",System.currentTimeMillis());
  }
  void watchGame()throws Exception{
    channels("SPORTS");ListView list=(ListView)get(a,"mCobraPlayerDrawerList");assertTrue(list.getCount()>0);View row=list.getChildAt(0);assertTrue(row instanceof CobraProUi.GameRow);click(row);
    ((CobraNavigationUiTest.PendingIo)get(a,"mIo")).drain();f.frames(2);measure();
  }
  @Test public void sportsChooserShowsFourCompleteRowsAndScrollsAllAdditionalChannels()throws Exception{
    for(int[] size:SIZES)for(int count:new int[]{3,4,7}){
      window(size[0],size[1]);open("sports",true);broadcasts(count);full();watchGame();ListView list=(ListView)tag("cobra_pro_broadcast_choices");assertNotNull(list);assertNull(get(a,"mCobraPlayerDrawer"));assertEquals(count,list.getCount());
      Rect area=rect(list);assertTrue("Four complete broadcast rows at "+width+"x"+height,list.getHeight()>=Math.min(count,4)*48);
      for(int i=0;i<Math.min(count,4);i++){View row=list.getChildAt(i);assertNotNull(row);Rect r=rect(row);assertTrue(area.contains(r));assertEquals(48,r.height());}
      assertSame(get(a,"mCobraActionSheet"),((ViewGroup)get(a,"mPlayerOverlay")).getChildAt(((ViewGroup)get(a,"mPlayerOverlay")).getChildCount()-1));
      screenshot("broadcasts-"+width+"x"+height+"-"+count);listIndex(list,count-1);click(list.getChildAt(count-1-list.getFirstVisiblePosition()));assertEquals("broadcast:"+(count-1),get(get(a,"mPlaying"),"id"));assertTrue(((InfinityLiveActivity.CobraMediaAudioState)call(a,"cobraMediaAudioState",get(a,"mPlayer"))).userMuted);
    }
  }
  @Test public void sportsChooserBackUsesExistingCloseOwner()throws Exception{
    open("sports",false);broadcasts(5);full();watchGame();assertNotNull(tag("cobra_pro_broadcast_choices"));ExoPlayer player=(ExoPlayer)get(a,"mPlayer");a.onBackPressed();measure();assertNull(get(a,"mCobraActionSheet"));assertSame(player,get(a,"mPlayer"));assertNotNull(get(a,"mPlayerOverlay"));
  }
  void repository()throws Exception{
    Class<?> type=Class.forName(InfinityLiveActivity.class.getName()+"$CobraSportsRepository");Object summary=construct("CobraSportsSummary");((List)get(summary,"lines")).addAll(Arrays.asList("Lions • Total yards 320","Packers • Total yards 280","LEADERS","Jared Goff • Passing 240"));
    Object repo=Proxy.newProxyInstance(type.getClassLoader(),new Class[]{type},(p,m,args)->{if(m.getName().equals("summary"))return summary;if(m.getName().equals("label"))return "Controlled summary";if(m.getName().equals("scoreboard"))return construct("CobraSportsBoardResult");return new ArrayList<>();});put(a,"mCobraSportsRepository",repo);
  }
  @Test public void miniAndFullscreenStatsKeepHomeMetadataAndEveryDetailedLeaderLine()throws Exception{
    for(boolean fullscreen:new boolean[]{false,true}){open("sports",false);repository();if(fullscreen){full();click(tag("cobra_fullscreen_sports_stats"));}else{CobraProUi.Hero h=(CobraProUi.Hero)get(a,"mCobraProHeroUi");h.revealControls();measure();click(h.player[6]);}
      View owner=(View)get(a,"mCobraActionSheet");assertNotNull(owner);((CobraNavigationUiTest.PendingIo)get(a,"mIo")).drain();f.frames(2);measure();String actual=text(owner);
      for(String expected:new String[]{"Away","Home","Packers","Lions","Ford Field","Kickoff","Total yards 320","LEADERS","Jared Goff"})assertTrue(expected+" missing",actual.contains(expected));
      assertEquals(fullscreen,tag("cobra_pro_stats_panel")!=null);screenshot(fullscreen?"fullscreen-stats":"mini-stats");
    }
  }
  @Test public void hiddenScoresStillRequireOriginalSpoilerConfirmation()throws Exception{
    open("sports",false);prefs.edit().putBoolean("cobra_sports_hide_scores",true).commit();full();click(tag("cobra_fullscreen_sports_stats"));assertEquals("sports-reveal-stats",get(a,"mCobraSheetKind"));assertNull(tag("cobra_pro_stats_panel"));assertFalse(text((View)get(a,"mCobraActionSheet")).contains("Total yards"));
  }
  @Test public void delayedStatsCannotPopulateAReplacedSheetOrDifferentMode()throws Exception{
    open("sports",false);repository();full();click(tag("cobra_fullscreen_sports_stats"));View old=(View)get(a,"mCobraActionSheet");call(a,"cobraSwitchMode","compact");((CobraNavigationUiTest.PendingIo)get(a,"mIo")).drain();f.frames(2);measure();assertFalse(old.isAttachedToWindow());assertNull(tag("cobra_pro_stats_panel"));assertFalse(text(decor()).contains("Jared Goff"));checkControls("compact");
  }
  @Test public void headerThemeUpdatesWithoutMovingItsExistingChildren()throws Exception{
    open("focus",false);ViewGroup header=(ViewGroup)get(a,"mCobraModeToolbar");assertEquals(4,header.getChildCount());int[] widths=new int[4];for(int i=0;i<4;i++)widths[i]=header.getChildAt(i).getWidth();
    for(String mode:new String[]{"light","dark","oled","system"}){prefs.edit().putString("cobra_appearance_mode",mode).commit();call(a,"cobraRefreshVisualEffects");measure();assertEquals(4,header.getChildCount());for(int i=0;i<4;i++)assertEquals(widths[i],header.getChildAt(i).getWidth());assertNotNull(header.getBackground());}
    call(a,"cobraSwitchMode","compact");measure();assertFalse((Boolean)call(get(a,"mCobraSix"),"pro"));assertFalse(header.isAttachedToWindow());
  }
  @Test public void actualActivityRecreationDoesNotRestoreProControlsIntoCompact()throws Exception{
    close();RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");
    ActivityController<InfinityLiveActivity> controller=Robolectric.buildActivity(InfinityLiveActivity.class).setup().visible();
    InfinityLiveActivity original=controller.get();SharedPreferences saved=(SharedPreferences)get(original,"mPrefs");saved.edit().putString("guide_view_mode","compact").commit();
    controller.recreate();InfinityLiveActivity restored=controller.get();assertNotSame(original,restored);
    View root=restored.getWindow().getDecorView();assertTrue(root.isAttachedToWindow());assertNull(root.findViewWithTag("cobra_fullscreen_sports_stats"));assertNull(root.findViewWithTag("cobra_pro_fullscreen_scroll"));assertNull(root.findViewWithTag("cobra_pro_stats_panel"));controller.pause().stop().destroy();
  }
}
