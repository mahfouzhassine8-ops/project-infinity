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

/** Actual signed433 Cards fullscreen chrome and original native More sheet.
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
  JSONObject report=new JSONObject().put("fixture","ACTUAL_SIGNED433_DEX_NATIVE_FULLSCREEN_CARDS_FRONT; state-onlyExoPlayer")
   .put("layout_trace",layoutTrace).put("controls",controls).put("more_before",before).put("callback_count",moreCalls).put("sheet_kind",String.valueOf(get(f.a,"mCobraSheetKind"))).put("sheet",visibility(sheet)).put("anchor",visibility(anchor)).put("pane",visibility(pane)).put("anchor_is_fullscreen_overlay",anchor==overlay).put("same_player",player==get(f.a,"mPlayer")).put("same_channel",channel==get(f.a,"mPlaying"));
  JSONArray children=new JSONArray();if(sheet instanceof ViewGroup)for(int i=0;i<((ViewGroup)sheet).getChildCount();i++)children.put(visibility(((ViewGroup)sheet).getChildAt(i)));report.put("sheet_children",children);
  Path out=Paths.get(System.getProperty("fold.output"));Files.createDirectories(out);Files.write(out.resolve("SIGNED433-FULLSCREEN-MORE-"+phase+".json"),(report.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
  org.robolectric.shadows.ShadowChoreographer.setPaused(true);
  assertEquals("Actual coordinate tap reaches existing settings handler once",1,moreCalls);
 }
}
