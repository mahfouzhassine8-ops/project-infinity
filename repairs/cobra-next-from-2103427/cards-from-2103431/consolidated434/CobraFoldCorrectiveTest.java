package com.projectinfinity.kodi;
import android.app.Application;
import android.graphics.Rect;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import java.util.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadow.api.Shadow;

/** Actual compiled owner Cards fullscreen chrome and original native More sheet.
 * State-only player, no decoder/provider workers, no application shutdown. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w358dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraFoldCorrectiveTest.Trace.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraFoldCorrectiveTest {
 static int moreCalls;
 @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true)
 public static class Trace extends CobraCardsLayoutTest.TerminalActions {
  @RealObject InfinityLiveActivity actual;
  @Implementation protected void showPlayerSettingsDrawer(){moreCalls++;Shadow.directlyOn(actual,InfinityLiveActivity.class,"showPlayerSettingsDrawer");}
 }
 static Object get(Object o,String n)throws Exception{return CobraCardsLayoutTest.get(o,n);}
 static void set(Object o,String n,Object v)throws Exception{CobraCardsLayoutTest.set(o,n,v);}
 static Object call(Object o,String n,Object...v)throws Exception{return CobraCardsLayoutTest.call(o,n,v);}
 static List<View> tree(View v){List<View> a=new ArrayList<>();a.add(v);if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)a.addAll(tree(((ViewGroup)v).getChildAt(i)));return a;}
 static JSONObject visibility(View v)throws Exception{
  if(v==null)return new JSONObject().put("exists",false);
  Rect r=new Rect();boolean visible=v.getGlobalVisibleRect(r);
  return new JSONObject().put("exists",true).put("class",v.getClass().getName()).put("tag",String.valueOf(v.getTag())).put("attached",v.isAttachedToWindow()).put("shown",v.isShown()).put("global_rect",new JSONArray(new int[]{r.left,r.top,r.right,r.bottom})).put("globally_visible",visible).put("alpha",v.getAlpha()).put("width",v.getWidth()).put("height",v.getHeight());
 }
 @Before public void nativeSetup()throws Exception{new CobraCardsLayoutTest().frames();moreCalls=0;}
 @Test public void signed433FrontFullscreenMoreCoordinateTrace()throws Exception{fullscreenTrace(941,1672,420,"PAUSED");}
 @Test public void signed433FullscreenMoreAnimationAndTallTrace()throws Exception{
  throw new AssertionError("NOT SELECTED: unpaused ActivityController.visible exhausts observer queue before feature execution; retained evidence, use bounded layout input instead");
 }
 @Test public void signed433FullscreenMoreReducedMotionLayoutTrace()throws Exception {
  fullscreenTrace(1080,2520,480,"REDUCED_MOTION_LAYOUT");
 }
 @Test public void signed433FullscreenMoreManualFrameTrace()throws Exception {
  fullscreenTrace(941,1672,420,"REDUCED_MOTION_LAYOUT");
  org.robolectric.util.ReflectionHelpers.callStaticMethod(android.animation.ValueAnimator.class,"setDurationScale",org.robolectric.util.ReflectionHelpers.ClassParameter.from(float.class,1f));
  fullscreenTrace(941,1672,420,"MANUAL_VSYNC");fullscreenTrace(1080,2520,480,"TALL_MANUAL_VSYNC");
 }
 @Test public void signed433HiddenRetainedMultiLayerMoreTrace()throws Exception {fullscreenTrace(1080,2520,480,"HIDDEN_MULTI_MANUAL_VSYNC");}
 @Test public void correctedFrontFullscreenMoreMenuVisibilityAndBack()throws Exception {
  assertTrue(Boolean.getBoolean("fold.candidate"));fullscreenTrace(1080,2520,480,"HIDDEN_MULTI_MANUAL_VSYNC");
 }
 @Test public void frontCardsOnlySheetHostOwnership()throws Exception {
  assertTrue(Boolean.getBoolean("fold.candidate"));JSONArray cases=new JSONArray();
  for(String mode:new String[]{"cards","mobile","compact","grid","focus"}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture(mode,1080,2520,480);
   FrameLayout overlay=new FrameLayout(f.a);((FrameLayout)f.a.findViewById(android.R.id.content)).addView(overlay,new FrameLayout.LayoutParams(-1,-1));set(f.a,"mPlayerOverlay",overlay);f.frames();
   assertEquals("Only front Cards owns this host override",mode.equals("cards")?overlay:null,CobraCardsLayout.frontPlayerSheetHost(f.a,"player-settings"));
   for(String kind:new String[]{"channel-actions","display","multi-settings",""})assertNull(CobraCardsLayout.frontPlayerSheetHost(f.a,kind));
   set(f.a,"mCobraProActive",true);assertNull(CobraCardsLayout.frontPlayerSheetHost(f.a,"player-settings"));set(f.a,"mCobraProActive",false);
   set(f.a,"mCobraProSportsActive",true);assertNull(CobraCardsLayout.frontPlayerSheetHost(f.a,"player-settings"));set(f.a,"mCobraProSportsActive",false);
   overlay.setVisibility(View.GONE);assertNull(CobraCardsLayout.frontPlayerSheetHost(f.a,"player-settings"));
   cases.put(mode);
  }
  CobraCardsLayoutTest.Fixture inner=new CobraCardsLayoutTest.Fixture("cards",1600,1680,320);FrameLayout overlay=new FrameLayout(inner.a);((FrameLayout)inner.a.findViewById(android.R.id.content)).addView(overlay,new FrameLayout.LayoutParams(-1,-1));set(inner.a,"mPlayerOverlay",overlay);inner.frames();assertNull(CobraCardsLayout.frontPlayerSheetHost(inner.a,"player-settings"));
  Path out=Paths.get(System.getProperty("fold.output"));Files.createDirectories(out);Files.write(out.resolve("FRONT-CARDS-ONLY-HOST-GUARD.json"),(new JSONObject().put("preserved_modes",cases).put("inner_unchanged",true).put("other_menu_kinds_unchanged",true).put("Pro_ProSports_unchanged",true).toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
 }
 static void framePulse() {
  Shadows.shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));
  Object receiver=org.robolectric.util.ReflectionHelpers.getField(Choreographer.getInstance(),"mDisplayEventReceiver");
  Object shadow=Shadow.extract(receiver);
  org.robolectric.util.ReflectionHelpers.callInstanceMethod(shadow,"onVsync");
  Shadows.shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));
 }
 void fullscreenTrace(int w,int h,int dpi,String phase)throws Exception{
  org.robolectric.shadows.ShadowChoreographer.setPaused(true);
  moreCalls=0;CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",w,h,dpi);
  f.player(true);
  Object player=f.player,channel=f.channels.get(0);set(f.a,"mPlayer",player);set(f.a,"mPlaying",channel);set(f.a,"mCobraPreviewPlayer",null);
  FrameLayout hiddenMulti=null;
  if(phase.contains("HIDDEN_MULTI")){
   hiddenMulti=new FrameLayout(f.a);((FrameLayout)f.a.findViewById(android.R.id.content)).addView(hiddenMulti,new FrameLayout.LayoutParams(-1,-1));set(f.a,"mMultiOverlay",hiddenMulti);f.frames();hiddenMulti.setVisibility(View.GONE);set(f.a,"mCobraMultiFullscreenActive",true);
  }
  FrameLayout overlay=new FrameLayout(f.a);overlay.setBackgroundColor(0xff000000);
  ((FrameLayout)f.a.findViewById(android.R.id.content)).addView(overlay,new FrameLayout.LayoutParams(-1,-1));set(f.a,"mPlayerOverlay",overlay);f.frames();
  call(f.a,"cobraBuildPlayerChrome");f.frames();View chrome=(View)get(f.a,"mPlayerChrome");
  List<View> mores=new ArrayList<>();JSONArray controls=new JSONArray();
  for(View v:tree(chrome))if(v.getClass().getName().endsWith("$CobraIconButton")){
   String glyph=String.valueOf(get(v,"glyph"));controls.put(new JSONObject().put("glyph",glyph).put("caption",get(v,"caption")).put("view",visibility(v)));if(glyph.equals("more"))mores.add(v);
  }
  assertEquals("Only actual fullscreen More",1,mores.size());View more=mores.get(0);assertTrue(more.hasOnClickListeners());JSONObject before=visibility(more);
  if(phase.equals("REDUCED_MOTION_LAYOUT"))org.robolectric.util.ReflectionHelpers.callStaticMethod(android.animation.ValueAnimator.class,"setDurationScale",org.robolectric.util.ReflectionHelpers.ClassParameter.from(float.class,0f));
  f.press(more);f.frames();
  JSONArray layoutTrace=new JSONArray();
  if(phase.equals("REDUCED_MOTION_LAYOUT")||phase.contains("MANUAL_VSYNC")) for(int i=0;i<20;i++) {
   View root=(View)get(f.a,"mCobraActionSheet"),panel=(View)get(f.a,"mCobraSheetPanel");
   JSONObject st=visibility(panel).put("layout_requested",panel.isLayoutRequested()).put("measured_w",panel.getMeasuredWidth()).put("measured_h",panel.getMeasuredHeight());
   android.widget.FrameLayout.LayoutParams lp=(android.widget.FrameLayout.LayoutParams)panel.getLayoutParams();
   st.put("lp",new JSONArray(new int[]{lp.width,lp.height,lp.leftMargin,lp.topMargin,lp.gravity}));layoutTrace.put(st);
   root.getViewTreeObserver().dispatchOnGlobalLayout();
   if(phase.contains("MANUAL_VSYNC"))framePulse();
   f.frames();
  }
  View sheet=(View)get(f.a,"mCobraActionSheet"),anchor=(View)get(f.a,"mCobraSheetAnchor"),pane=(View)get(f.a,"mCobraSheetPane");
  boolean candidate=Boolean.getBoolean("fold.candidate");
  JSONObject report=new JSONObject().put("fixture",(candidate?"ACTUAL_COMPILED434":"ACTUAL_SIGNED433")+"_DEX_NATIVE_FULLSCREEN_CARDS_FRONT; state-onlyExoPlayer")
   .put("layout_trace",layoutTrace).put("controls",controls).put("more_before",before).put("callback_count",moreCalls).put("sheet_kind",String.valueOf(get(f.a,"mCobraSheetKind"))).put("sheet",visibility(sheet)).put("anchor",visibility(anchor)).put("pane",visibility(pane)).put("anchor_is_fullscreen_overlay",anchor==overlay).put("sheet_parent_is_player",sheet!=null&&sheet.getParent()==overlay).put("sheet_parent_is_hidden_multi",hiddenMulti!=null&&sheet!=null&&sheet.getParent()==hiddenMulti).put("retained_multi",visibility(hiddenMulti)).put("same_player",player==get(f.a,"mPlayer")).put("same_channel",channel==get(f.a,"mPlaying"));
  JSONArray children=new JSONArray();if(sheet instanceof ViewGroup)for(int i=0;i<((ViewGroup)sheet).getChildCount();i++)children.put(visibility(((ViewGroup)sheet).getChildAt(i)));report.put("sheet_children",children);
  Path out=Paths.get(System.getProperty("fold.output"));Files.createDirectories(out);Files.write(out.resolve((candidate?"CANDIDATE434":"SIGNED433")+"-FULLSCREEN-MORE-"+phase+".json"),(report.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
  org.robolectric.shadows.ShadowChoreographer.setPaused(true);
  assertEquals("Actual coordinate tap reaches existing settings handler once",1,moreCalls);
  assertSame(player,get(f.a,"mPlayer"));assertSame(channel,get(f.a,"mPlaying"));
  if(phase.contains("HIDDEN_MULTI")){
   assertSame(hiddenMulti,get(f.a,"mMultiOverlay"));assertEquals(View.GONE,hiddenMulti.getVisibility());
   if(!candidate){assertSame("Reproduce original wrong host",hiddenMulti,sheet.getParent());assertFalse("Original hidden-host menu is invisible",sheet.isShown());return;}
   assertSame("Visible fullscreen player owns original menu",overlay,sheet.getParent());assertTrue(sheet.isShown());assertTrue(((View)get(f.a,"mCobraSheetPanel")).getAlpha()>.99f);
   boolean heading=false;for(View v:tree(sheet))if(v instanceof TextView)heading|=((TextView)v).getText().toString().equals("Player settings");assertTrue("Original menu content",heading);
   long t=android.os.SystemClock.uptimeMillis();f.a.dispatchKeyEvent(new KeyEvent(t,t,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_BACK,0));f.a.dispatchKeyEvent(new KeyEvent(t,t+32,KeyEvent.ACTION_UP,KeyEvent.KEYCODE_BACK,0));f.frames();
   assertNull("Actual Back closes only the sheet",get(f.a,"mCobraActionSheet"));assertSame(overlay,get(f.a,"mPlayerOverlay"));assertSame(player,get(f.a,"mPlayer"));assertSame(channel,get(f.a,"mPlaying"));assertSame(hiddenMulti,get(f.a,"mMultiOverlay"));
   call(f.a,"showPlayerChromeTemporarily");f.frames();f.press(more);f.frames();for(int i=0;i<20;i++){((View)get(f.a,"mCobraActionSheet")).getViewTreeObserver().dispatchOnGlobalLayout();framePulse();f.frames();}
   View reopened=(View)get(f.a,"mCobraActionSheet");assertEquals(2,moreCalls);assertSame(overlay,reopened.getParent());assertTrue(reopened.isShown());assertTrue(((View)get(f.a,"mCobraSheetPanel")).getAlpha()>.99f);assertSame(player,get(f.a,"mPlayer"));
   Files.write(out.resolve("MORE-ACTUAL-TOUCH-BACK-REOPEN.json"),(new JSONObject().put("actual_pointer_presses",2).put("native_Back_closes_only_sheet",true).put("menu_visible_after_both_presses",true).put("player_channel_retained",true).put("hidden_MultiView_untouched",true).toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
  }
 }
}
