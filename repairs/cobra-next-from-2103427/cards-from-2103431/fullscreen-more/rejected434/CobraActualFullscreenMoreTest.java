package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.Rect;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadow.api.Shadow;
import org.robolectric.shadows.ShadowActivity;
import org.robolectric.util.ReflectionHelpers;

/** Actual shipped owner UI and production fullscreen entry/listeners.
 * State-only ExoPlayer proxy, synthetic inventory; no decoder/network/shutdown.
 * No replacement fullscreen overlay, promotion, visibility or global-layout dispatch. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w360dp-h840dp-port-480dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraActualFullscreenMoreTest.Trace.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraActualFullscreenMoreTest {
 static int moreCalls,visualCalls,chromeBuilds,positionCalls;
 static JSONArray positionTrace=new JSONArray();
 @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true)
 public static class Trace extends ShadowActivity {
  @RealObject InfinityLiveActivity owner;
  @Implementation protected void showPlayerSettingsDrawer(){moreCalls++;Shadow.directlyOn(owner,InfinityLiveActivity.class,"showPlayerSettingsDrawer");}
  @Implementation protected void cobraShowVisualMenu(View anchor){visualCalls++;Shadow.directlyOn(owner,InfinityLiveActivity.class,"cobraShowVisualMenu",ReflectionHelpers.ClassParameter.from(View.class,anchor));}
  @Implementation protected void cobraBuildPlayerChrome(){chromeBuilds++;Shadow.directlyOn(owner,InfinityLiveActivity.class,"cobraBuildPlayerChrome");}
  @Implementation protected void cobraPositionAnchoredSheet(FrameLayout root,LinearLayout panel,View anchor,View pane)throws Exception{positionCalls++;JSONObject row=new JSONObject().put("before",panelState(panel)).put("height_limit_before",get(owner,"mCobraSheetHeightLimit"));Shadow.directlyOn(owner,InfinityLiveActivity.class,"cobraPositionAnchoredSheet",ReflectionHelpers.ClassParameter.from(FrameLayout.class,root),ReflectionHelpers.ClassParameter.from(LinearLayout.class,panel),ReflectionHelpers.ClassParameter.from(View.class,anchor),ReflectionHelpers.ClassParameter.from(View.class,pane));row.put("after",panelState(panel)).put("height_limit_after",get(owner,"mCobraSheetHeightLimit"));if(positionTrace.length()<200)positionTrace.put(row);}
 }
 static Object get(Object o,String n)throws Exception{return CobraCardsLayoutTest.get(o,n);}
 static Object call(Object o,String n,Object...v)throws Exception{return CobraCardsLayoutTest.call(o,n,v);}
 static Path out(){return Paths.get(System.getProperty("rejected434.output"));}
 static void save(String name,JSONObject value)throws Exception{Files.createDirectories(out());Files.write(out().resolve(name+".json"),(value.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}
 @Before public void start(){new CobraCardsLayoutTest().frames();moreCalls=0;visualCalls=0;chromeBuilds=0;positionCalls=0;positionTrace=new JSONArray();}
 static void pulses(int count){
  for(int i=0;i<count;i++){
   Shadows.shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));
   Object receiver=ReflectionHelpers.getField(Choreographer.getInstance(),"mDisplayEventReceiver");
   ReflectionHelpers.callInstanceMethod(Shadow.extract(receiver),"onVsync");
   Shadows.shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));
  }
 }
 static JSONObject visible(View v)throws Exception{if(v==null)return new JSONObject().put("exists",false);Rect r=new Rect();boolean yes=v.getGlobalVisibleRect(r);return new JSONObject().put("exists",true).put("attached",v.isAttachedToWindow()).put("shown",v.isShown()).put("globally_visible",yes).put("global_rect",new JSONArray(new int[]{r.left,r.top,r.right,r.bottom})).put("alpha",v.getAlpha()).put("width",v.getWidth()).put("height",v.getHeight());}
 static java.util.List<View> tree(View v){java.util.List<View> a=new java.util.ArrayList<>();a.add(v);if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)a.addAll(tree(((ViewGroup)v).getChildAt(i)));return a;}
 static JSONObject panelState(LinearLayout p)throws Exception{FrameLayout.LayoutParams lp=(FrameLayout.LayoutParams)p.getLayoutParams();return visible(p).put("requested",p.isLayoutRequested()).put("measured_w",p.getMeasuredWidth()).put("measured_h",p.getMeasuredHeight()).put("left",p.getLeft()).put("top",p.getTop()).put("lp",new JSONArray(new int[]{lp.width,lp.height,lp.leftMargin,lp.topMargin,lp.gravity}));}
 static View icon(View root,String glyph)throws Exception{
  for(View v:tree(root))if(v.getClass().getName().endsWith("$CobraIconButton") && glyph.equals(get(v,"glyph")))return v;
  throw new AssertionError("Actual visible icon missing: "+glyph);
 }
 static CobraCardsLayoutTest.Fixture fixture()throws Exception{
  CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1080,2520,480);f.a.getWindow().setLayout(1080,2520);pulses(3);return f;
 }
 static void actualPreviewPress(CobraCardsLayoutTest.Fixture f)throws Exception{
  f.player(true);View preview=(View)get(f.a,"mCobraPreviewHost");assertTrue(preview.hasOnClickListeners());
  // Actual video-area center, clear of the bottom-right PiP target.
  f.press(preview);pulses(8);
  assertEquals("Production handoff must execute, not TerminalActions shadow",1,get(f.a,"mCobraPreviewHandoffs"));
  assertSame(f.player,get(f.a,"mPlayer"));assertNull(get(f.a,"mCobraPreviewPlayer"));
  View overlay=(View)get(f.a,"mPlayerOverlay");assertNotNull(overlay);assertTrue(overlay.isAttachedToWindow());
  assertSame("Production fullscreen is the actual Decor child",f.a.getWindow().getDecorView(),overlay.getParent());
 }
 static JSONObject report(CobraCardsLayoutTest.Fixture f)throws Exception{
  return new JSONObject().put("actual_production_overlay",visible((View)get(f.a,"mPlayerOverlay")))
   .put("sheet",visible((View)get(f.a,"mCobraActionSheet"))).put("panel",visible((View)get(f.a,"mCobraSheetPanel")))
   .put("anchor",visible((View)get(f.a,"mCobraSheetAnchor"))).put("pane",visible((View)get(f.a,"mCobraSheetPane")))
   .put("kind",get(f.a,"mCobraSheetKind")).put("more_callbacks",moreCalls).put("visual_callbacks",visualCalls)
   .put("position_trace",positionTrace).put("native_chrome_builds",chromeBuilds).put("native_position_callbacks",positionCalls)
   .put("handoffs",get(f.a,"mCobraPreviewHandoffs")).put("same_player",f.player==get(f.a,"mPlayer"))
   .put("new_recorded_io",f.io.admitted.size()).put("global_layout_manually_dispatched",false);
 }
 static void assertSheetVisible(CobraCardsLayoutTest.Fixture f,String kind)throws Exception{
  View sheet=(View)get(f.a,"mCobraActionSheet"),panel=(View)get(f.a,"mCobraSheetPanel");
  assertNotNull("Original sheet still exists",sheet);assertNotNull(panel);assertEquals(kind,get(f.a,"mCobraSheetKind"));
  assertTrue("Original panel actually shown",panel.isShown());Rect bounds=new Rect();assertTrue("Original panel has visible screen bounds",panel.getGlobalVisibleRect(bounds));
  assertTrue("Normal native animation completed without forced alpha",panel.getAlpha()>.99f);
 }
 @Test public void actualPreviewFullscreenThenMoreUsesProductionOverlay()throws Exception{
  CobraCardsLayoutTest.Fixture f=fixture();actualPreviewPress(f);View more=icon((View)get(f.a,"mPlayerChrome"),"more");f.press(more);pulses(20);
  save("ACTUAL-PREVIEW-FULLSCREEN-MORE",report(f));assertEquals(1,moreCalls);assertSheetVisible(f,"player-settings");assertSame(f.player,get(f.a,"mPlayer"));
 }
 @Test public void actualFullscreenMenuSurvivesNativeChromeRevealAndLayout()throws Exception{
  CobraCardsLayoutTest.Fixture f=fixture();actualPreviewPress(f);View overlay=(View)get(f.a,"mPlayerOverlay");
  pulses(130); // Original four-second chrome timer, no production timer change.
  f.press(overlay);pulses(4);View more=icon((View)get(f.a,"mPlayerChrome"),"more");f.press(more);pulses(20);
  save("ACTUAL-CHROME-REVEAL-MORE",report(f));assertSheetVisible(f,"player-settings");
  long t=android.os.SystemClock.uptimeMillis();f.a.dispatchKeyEvent(new KeyEvent(t,t,KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_BACK,0));f.a.dispatchKeyEvent(new KeyEvent(t,t+32,KeyEvent.ACTION_UP,KeyEvent.KEYCODE_BACK,0));pulses(3);
  assertNull(get(f.a,"mCobraActionSheet"));assertSame(overlay,get(f.a,"mPlayerOverlay"));assertSame(f.player,get(f.a,"mPlayer"));
 }
 @Test public void actualCardsSunOpensOriginalMenuAndAppliesNightCinemaOff()throws Exception{
  CobraCardsLayoutTest.Fixture f=fixture();f.player(true);View button=((View)get(f.a,"mCobraModeToolbar")).findViewWithTag("cobra_mode_visuals");assertNotNull(button);
  f.press(button);pulses(20);save("ACTUAL-CARDS-SUN-VISUALS",report(f));assertEquals(1,visualCalls);assertSheetVisible(f,"visual-settings");
  View sheet=(View)get(f.a,"mCobraActionSheet"),off=sheet.findViewWithTag("cobra-visual-night:off");assertNotNull("Original Night Cinema off action",off);f.press(off);pulses(10);assertFalse(f.prefs.getBoolean("cobra_night_cinema",true));
 }
}
