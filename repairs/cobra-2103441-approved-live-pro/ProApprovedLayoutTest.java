package com.projectinfinity.kodi;

import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.*;
import android.widget.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import org.json.*;
import org.junit.*;
import org.robolectric.*;
import static org.junit.Assert.*;

/** Actual compiled owner views and decor input; synthetic channels/controlled decoder. */
@org.robolectric.annotation.Config(shadows={ProApprovedLayoutTest.Actions.class})
public class ProApprovedLayoutTest extends ApprovedLiveProTest {
 @org.robolectric.annotation.Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true,looseSignatures=true)
 public static class Actions extends PlayingRowAndProViewportTest.Trace {
  @org.robolectric.annotation.Implementation protected void playChannel(Object channel){playRequests++;requestedChannel=channel;}
 }
 static int playRequests;static Object requestedChannel;
 static AbsListView list(CobraCardsLayoutTest.Fixture f)throws Exception{return (AbsListView)get(f.a,"mCobraGuideList");}
 static View hero(CobraCardsLayoutTest.Fixture f)throws Exception{return (View)get(f.a,"mCobraProHeroUi");}
 static void watching(CobraCardsLayoutTest.Fixture f)throws Exception {
  put(f.a,"mCobraProPlaybackOwned",true);put(f.a,"mCobraProState",2);
  call(f.a,"cobraRefreshProHero");call(f.a,"cobraLayoutGuide");frames();
 }
 static CobraCardsLayoutTest.Fixture pro(int[] size,String theme)throws Exception {
  CobraCardsLayoutTest.Fixture f=fixture("cards",size[0],size[1],size[2],theme);interactivePlayer(f);f.mode("focus");watching(f);return f;
 }
 static void interactivePlayer(CobraCardsLayoutTest.Fixture f)throws Exception {
  Object prior=f.player;CobraCardsLayoutTest.Playback state=f.input;
  androidx.media3.common.MediaItem media=new androidx.media3.common.MediaItem.Builder().setUri("https://example.invalid/live").setLiveConfiguration(new androidx.media3.common.MediaItem.LiveConfiguration.Builder().build()).build();
  androidx.media3.common.Timeline timeline=new androidx.media3.exoplayer.source.SinglePeriodTimeline(3600000000L,true,true,true,null,media);
  f.player=java.lang.reflect.Proxy.newProxyInstance(androidx.media3.exoplayer.ExoPlayer.class.getClassLoader(),new Class<?>[]{androidx.media3.exoplayer.ExoPlayer.class},(obj,method,args)->{
   String name=method.getName();if(name.equals("getCurrentTimeline"))return timeline;if(name.equals("isCurrentMediaItemLive"))return true;
   if(name.equals("pause")){state.ready=false;return null;}if(name.equals("play")){state.ready=true;return null;}if(name.equals("setPlayWhenReady")){state.ready=(Boolean)args[0];return null;}
   return state.invoke(obj,method,args);
  });
  f.binding=CobraCardsLayoutTest.construct("CobraPlayerBinding",f.a,f.player,f.channels.get(0));Map bindings=(Map)get(f.a,"mCobraPlayerBindings");bindings.remove(prior);bindings.put(f.player,f.binding);put(f.a,"mCobraPreviewPlayer",f.player);
 }
 static View[] navigation(CobraCardsLayoutTest.Fixture f)throws Exception{
  ViewGroup browser=(ViewGroup)get(f.a,"mCobraGuideBrowser");
  for(int i=0;i<browser.getChildCount();i++){View v=browser.getChildAt(i);if(v.getClass().getSimpleName().equals("Filters"))return (View[])get(v,"buttons");}
  throw new AssertionError("Original Pro filters missing");
 }
 static void paired(CobraCardsLayoutTest.Fixture f)throws Exception {
  assertTrue("Expanded Pro uses a two-column channel grid",list(f) instanceof GridView);
  GridView grid=(GridView)list(f);assertEquals(2,grid.getNumColumns());assertTrue(grid.getChildCount()>=4);
  View left=grid.getChildAt(0),right=grid.getChildAt(1);Rect a=bounds(left),b=bounds(right);
  assertEquals(a.top,b.top);assertTrue(a.right<b.left);assertEquals(a.width(),b.width());
  assertEquals("ChannelRow",left.getClass().getSimpleName());
  for(View row:new View[]{left,right})for(String part:new String[]{"number","logo","name","program","time","progress","play"}){
   View child=(View)get(row,part);assertFalse(part+" must have real visible bounds",bounds(child).isEmpty());
   assertTrue(part+" remains inside channel row",bounds(row).contains(bounds(child)));
  }
  assertTrue("Channel text receives usable width",((View)get(left,"name")).getWidth()>left.getWidth()*.45f);
 }
 static void originalGeometry(CobraCardsLayoutTest.Fixture f)throws Exception {
  Object model=get(f.a,"mCobraModeLayout");int w=(int)get(model,"width"),h=(int)get(model,"height");
  int state=!(Boolean)get(f.a,"mCobraProPlaybackOwned")&&get(f.a,"mCobraPreviewPlayer")!=null?1:(int)get(f.a,"mCobraProState");
  int[][] original=(int[][])callPro("sportsGeometry",w,h,f.a.getResources().getConfiguration().fontScale,state,(float)get(f.a,"mCobraProSportsCollapse"));
  for(int i=0;i<4;i++)assertArrayEquals("Original cover/Pro Sports geometry",original[i],(int[])get(model,new String[]{"toolbar","video","details","browser"}[i]));
 }
 @Test public void proApprovedInnerAndFrontPreservation()throws Exception {
  JSONArray cases=new JSONArray();
  CobraCardsLayoutTest.Fixture cover=fixture("cards",1080,2520,480,"dark");cover.mode("focus");put(cover.a,"mCobraProState",2);call(cover.a,"cobraLayoutGuide");frames();
  JSONObject old=new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("cards.layout.output"),"BASELINE-PRO-GEOMETRY.json")),StandardCharsets.UTF_8)).getJSONArray("cases").getJSONObject(0);
  assertNull("Exact recorded accepted-baseline front geometry",CobraCardsLayoutTest.diff(old,cover.geometry(),"front"));
  assertTrue(list(cover) instanceof ListView);watching(cover);originalGeometry(cover);
  for(int[] size:new int[][]{{1600,1800,240},{1800,1600,240},{1536,1024,160}})for(String theme:new String[]{"dark","light"}){
   CobraCardsLayoutTest.Fixture f=pro(size,theme);paired(f);Object model=get(f.a,"mCobraModeLayout");
   int[] video=(int[])get(model,"video"),details=(int[])get(model,"details"),browser=(int[])get(model,"browser");
   assertEquals(video[1],details[1]);assertEquals(video[3],details[3]);assertTrue(video[0]+video[2]<details[0]);
   assertTrue(browser[1]>video[1]+video[3]);assertEquals(8,browser[0]);assertEquals((int)get(model,"width")-16,browser[2]);
   assertTrue("Channel area consumes remaining vertical space",browser[3]>(int)get(model,"height")*.4f);
   View info=(View)get(hero(f),"info");assertSame(get(f.a,"mCobraGuideDetails"),info.getParent());assertTrue(info.isShown());
   assertEquals(6,navigation(f).length);assertSame(f.player,get(f.a,"mCobraPreviewPlayer"));assertEquals(0,requests);
   image((View)get(f.a,"mCobraGuideShell"),"PRO-APPROVED-"+size[0]+"x"+size[1]+"-"+theme);
   cases.put(new JSONObject().put("viewport",new JSONArray(size)).put("theme",theme).put("geometry",f.geometry()).put("visible_channel_rows",list(f).getChildCount()).put("player_surface",bounds((View)get(f.a,"mCobraPreviewHost")).toShortString()));
   put(f.a,"mCobraProSportsActive",true);call(f.a,"cobraLayoutGuide");frames();originalGeometry(f);
  }
  save("PRO-APPROVED-GEOMETRY",new JSONObject().put("cases",cases).put("front_recorded_geometry","EXACT").put("reference_sha256","deb2e9f38ecc8d03ab5454675fc5d773303bc1cd54de8c7a97b940c510680840").put("video_decoder","CONTROLLED_NOT_RENDERED"));
 }
 static void longPress(CobraCardsLayoutTest.Fixture f,View target)throws Exception {
  Rect b=bounds(target);assertFalse(b.isEmpty());View root=f.a.getWindow().getDecorView();int[] xy=new int[2];root.getLocationOnScreen(xy);long t=SystemClock.uptimeMillis();
  MotionEvent down=MotionEvent.obtain(t,t,MotionEvent.ACTION_DOWN,b.exactCenterX()-xy[0],b.exactCenterY()-xy[1],0);assertTrue(root.dispatchTouchEvent(down));down.recycle();
  Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(ViewConfiguration.getLongPressTimeout()+100));
  MotionEvent up=MotionEvent.obtain(t,SystemClock.uptimeMillis(),MotionEvent.ACTION_UP,b.exactCenterX()-xy[0],b.exactCenterY()-xy[1],0);root.dispatchTouchEvent(up);up.recycle();frames();
 }
 static void reveal(CobraCardsLayoutTest.Fixture f)throws Exception {
  Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(4100));frames();assertFalse((Boolean)get(hero(f),"controlsVisible"));
  f.press(hero(f));frames();assertTrue("Real player tap reveals original controls",(Boolean)get(hero(f),"controlsVisible"));
 }
 static void pressControl(CobraCardsLayoutTest.Fixture f,int index)throws Exception {
  View target=((View[])get(hero(f),"player"))[index];
  target.requestRectangleOnScreen(new Rect(0,0,target.getWidth(),target.getHeight()),true);frames();f.press(target);frames();
 }
 @Test public void proNavigationRowsAndRealTouch()throws Exception {
  JSONArray cases=new JSONArray();for(String theme:new String[]{"dark","light"}){
   CobraCardsLayoutTest.Fixture f=pro(new int[]{1600,1800,240},theme);Object player=f.player,texture=get(f.a,"mCobraPreviewTexture");
   Set favorites=(Set)get(f.a,"mFavorites");for(int i=0;i<6;i++)favorites.add(get(f.channels.get(i),"id"));
   f.press(navigation(f)[1]);frames();assertEquals("FAVORITES",get(f.a,"mCategory"));assertEquals(6,list(f).getCount());paired(f);
   f.press(navigation(f)[0]);frames();assertEquals("ALL",get(f.a,"mCategory"));assertEquals(24,list(f).getCount());
   int plays=playRequests;Object target=list(f).getItemAtPosition(1);f.press((View)get(list(f).getChildAt(1),"play"));frames();assertEquals(plays+1,playRequests);assertSame("Original Play receives the tapped channel",target,requestedChannel);
   longPress(f,list(f).getChildAt(1));assertNotNull("Original row context menu opens from real long press",get(f.a,"mCobraActionSheet"));assertTrue(((View)get(f.a,"mCobraSheetPanel")).isShown());f.a.onBackPressed();frames();
   list(f).setSelectionFromTop(8,-17);frames();int first=list(f).getFirstVisiblePosition();int top=list(f).getChildAt(0).getTop();
   call(f.a,"cobraRememberModeScroll");call(f.a,"cobraRenderGuideBrowser");frames();assertEquals(first,list(f).getFirstVisiblePosition());assertEquals("Original pixel offset restored after browser refresh",top,list(f).getChildAt(0).getTop());
   watching(f);reveal(f);View[] controls=(View[])get(hero(f),"player");assertEquals(9,controls.length);
   pressControl(f,0);assertFalse("Original Pause dispatch reaches player",f.input.ready);pressControl(f,0);assertTrue(f.input.ready);
   pressControl(f,5);assertNotNull("Original More sheet opens",get(f.a,"mCobraActionSheet"));f.a.onBackPressed();frames();
   reveal(f);pressControl(f,4);assertNotNull("Fullscreen real press opens existing player",get(f.a,"mPlayerOverlay"));assertSame(player,get(f.a,"mPlayer"));
   View back=CobraActualFullscreenMoreTest.icon((View)get(f.a,"mPlayerChrome"),"back");f.press(back);frames();assertNull(get(f.a,"mPlayerOverlay"));assertSame(player,get(f.a,"mCobraPreviewPlayer"));
   watching(f);reveal(f);int before=pip;pressControl(f,8);assertEquals("Original PiP dispatch",before+1,pip);
   assertSame(texture,get(f.a,"mCobraPreviewTexture"));
   cases.put(new JSONObject().put("theme",theme).put("real_decor_input",true).put("favorites_all_context_scroll_pause_resume_more_fullscreen_pip",true));
  }save("PRO-APPROVED-REAL-TOUCH",new JSONObject().put("cases",cases).put("hardware_PiP_decoder","NOT_TESTED"));
 }
 static void resize(CobraCardsLayoutTest.Fixture f,int[] pane)throws Exception {
  RuntimeEnvironment.setQualifiers("w"+(pane[0]*160/pane[2])+"dp-h"+(pane[1]*160/pane[2])+"dp-"+(pane[0]>pane[1]?"land":"port")+"-"+pane[2]+"dpi");
  org.robolectric.shadows.ShadowDisplay d=Shadows.shadowOf(f.a.getWindowManager().getDefaultDisplay());d.setDensityDpi(pane[2]);d.setWidth(pane[0]);d.setHeight(pane[1]);d.setRealWidth(pane[0]);d.setRealHeight(pane[1]);f.a.getWindow().setLayout(pane[0],pane[1]);frames();
  View decor=f.a.getWindow().getDecorView();Object root=org.robolectric.util.ReflectionHelpers.callInstanceMethod(decor,"getViewRootImpl");((org.robolectric.shadows.ShadowViewRootImpl)org.robolectric.shadow.api.Shadow.extract(root)).callDispatchResized();
  decor.measure(View.MeasureSpec.makeMeasureSpec(pane[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(pane[1],View.MeasureSpec.EXACTLY));decor.layout(0,0,pane[0],pane[1]);call(f.a,"cobraLayoutGuide");frames();
 }
 @Test public void foldOrientationAndThemeRestoration()throws Exception {
  CobraCardsLayoutTest.Fixture f=pro(new int[]{1080,2520,480},"dark");Object player=f.player,texture=get(f.a,"mCobraPreviewTexture"),channel=get(f.a,"mGuidePreviewChannel");JSONArray phases=new JSONArray();
  for(int[] pane:new int[][]{{1600,1800,240},{1800,1600,240},{1080,2520,480},{2520,1080,480},{720,1400,320},{1600,1800,240}}){
   list(f).setSelectionFromTop(8,-12);frames();Object adapter=list(f).getAdapter();int oldPosition=list(f).getFirstVisiblePosition();Object leading=list(f).getItemAtPosition(oldPosition);
   resize(f,pane);Object model=get(f.a,"mCobraModeLayout");boolean expanded=(int)get(model,"width")>=700&&(int)get(model,"height")>=600;
   if(expanded)paired(f);else{assertTrue(list(f) instanceof ListView);originalGeometry(f);}
   assertEquals("Original viewport callback rebuilds the same native adapter type",adapter.getClass(),list(f).getAdapter().getClass());
   assertTrue("Leading channel stays visible across column change",list(f).getFirstVisiblePosition()<=oldPosition&&list(f).getLastVisiblePosition()>=oldPosition);
   assertSame(leading,list(f).getItemAtPosition(oldPosition));
   for(String theme:new String[]{"light","dark","oled"}){
    f.prefs.edit().putString("cobra_appearance_mode",theme).commit();call(f.a,"cobraRestyleGuide");frames();
    assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertSame(channel,get(f.a,"mGuidePreviewChannel"));
    assertEquals(expanded,list(f) instanceof GridView);
    phases.put(new JSONObject().put("viewport",new JSONArray(pane)).put("theme",theme).put("first_visible",list(f).getFirstVisiblePosition()).put("layout",f.geometry()));
   }
  }
  for(String mode:new String[]{"mobile","compact","grid","cards"}){f.mode(mode);assertFalse(list(f).getClass().getName().contains("ProExpanded"));f.mode("focus");watching(f);paired(f);assertSame(player,get(f.a,"mCobraPreviewPlayer"));}
  save("PRO-APPROVED-RESIZE-THEMES",new JSONObject().put("phases",phases).put("physical_fold","NOT_TESTED").put("same_player_texture_channel",true));
 }
}
