package com.projectinfinity.kodi;

import android.app.*;
import android.content.res.Configuration;
import android.graphics.Rect;
import android.os.Looper;
import android.view.*;
import android.widget.*;
import java.lang.reflect.Method;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadow.api.Shadow;
import org.robolectric.util.ReflectionHelpers;

/** Actual owner DEX translated to host; real native views, pointer dispatch and
 * frame callbacks. Synthetic inventory/state-only player; NOT Fold/decoder QA. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 instrumentedPackages={"com.projectinfinity.kodi"},shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraDrawerCorrectionTest {
 @Implements(className="android.view.ViewRootImpl",isInAndroidSdk=false)
 public static class InsetsInput extends org.robolectric.shadows.ShadowViewRootImpl {
  static WindowInsets supplied;
  @Implementation protected WindowInsets getWindowInsets(boolean force){return supplied==null?super.getWindowInsets(force):supplied;}
 }
 static Object get(Object a,String n)throws Exception{return CobraCardsLayoutTest.get(a,n);}
 static void set(Object a,String n,Object v)throws Exception{CobraCardsLayoutTest.set(a,n,v);}
 static Object call(Object a,String n,Object...v)throws Exception{return CobraCardsLayoutTest.call(a,n,v);}
 static boolean candidate(){return Boolean.getBoolean("drawer.candidate");}
 static Path output(){return Paths.get(System.getProperty("drawer.output"));}
 static void write(String name,Object value)throws Exception{Files.createDirectories(output());Files.write(output().resolve(name+".json"),(value.toString()+"\n").getBytes(StandardCharsets.UTF_8));}
 @Before public void init()throws Exception{new CobraCardsLayoutTest().frames();CobraCardsLayoutTest.nativeWarmThemeSetup();}
 static View view(CobraCardsLayoutTest.Fixture f,String n)throws Exception{return (View)get(f.a,n);}
 static void layout(CobraCardsLayoutTest.Fixture f,int w,int h){View root=f.a.getWindow().getDecorView();root.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));root.layout(0,0,w,h);}
 static void pulse(CobraCardsLayoutTest.Fixture f,int w,int h)throws Exception{
  Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));
  Object receiver=ReflectionHelpers.getField(Choreographer.getInstance(),"mDisplayEventReceiver");
  ReflectionHelpers.callInstanceMethod(Shadow.extract(receiver),"onVsync");
  Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));layout(f,w,h);
 }
 static void settle(CobraCardsLayoutTest.Fixture f,int w,int h)throws Exception{for(int i=0;i<12;i++)pulse(f,w,h);}
 static View drawer(CobraCardsLayoutTest.Fixture f){return f.a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");}
 static void open(CobraCardsLayoutTest.Fixture f)throws Exception{
  assertNull(drawer(f));View button=((ViewGroup)view(f,"mCobraModeToolbar")).getChildAt(0);
  assertTrue(button.hasOnClickListeners());f.press(button);assertNotNull("Real header pointer must create original drawer",drawer(f));
 }
 static JSONObject geometry(CobraCardsLayoutTest.Fixture f)throws Exception{
  JSONObject x=new JSONObject();
  for(String n:new String[]{"mCobraModeToolbar","mCobraGuideVideo","mCobraGuideDetails","mCobraGuideBrowser","mCobraGuideList"}){
   View v=view(f,n);x.put(n,new JSONArray(new int[]{v.getLeft(),v.getTop(),v.getWidth(),v.getHeight()}));
  }
  Object model=get(f.a,"mCobraModeLayout");
  View list=view(f,"mCobraGuideList");
  return x.put("model_width_dp",get(model,"width")).put("model_height_dp",get(model,"height")).put("columns",list instanceof GridView?((GridView)list).getNumColumns():1);
 }
 static JSONObject metrics(CobraCardsLayoutTest.Fixture f)throws Exception{
  View shell=view(f,"mCobraGuideShell"),stage=view(f,"mStage"),root=f.a.getWindow().getDecorView();int[] xy=new int[2];shell.getLocationInWindow(xy);
  return geometry(f).put("decor_width",root.getWidth()).put("shell_width",shell.getWidth()).put("shell_x",xy[0]).put("translation_x",stage.getTranslationX()).put("scale_x",stage.getScaleX()).put("IO_jobs",f.io.admitted.size());
 }
 static void same(Object a,Object b,String why)throws Exception{assertNull(why,CobraCardsLayoutTest.diff(a,b,why));}
 static void stable(CobraCardsLayoutTest.Fixture f,JSONObject before,int w,int h,int pulses,JSONArray trace)throws Exception{
  for(int i=0;i<pulses;i++){
   // Exercise BOTH original sizing consumers on animation frames. This is a
   // bounded test stimulus, never a production refresh/polling loop.
   call(f.a,"cobraLayoutGuide");call(f.a,"cobraRestyleGuide");pulse(f,w,h);
   same(before,geometry(f),"Cards layout during original drawer frame "+i);trace.put(metrics(f));
  }
 }
 @Test public void innerDrawerFramesRetainWidthAndState()throws Exception{
  assertTrue(candidate());CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1600,1680,320);f.a.getWindow().setLayout(1600,1680);settle(f,1600,1680);
  f.player(true);GridView grid=(GridView)view(f,"mCobraGuideList");grid.setSelection(8);settle(f,1600,1680);grid.scrollListBy(17);settle(f,1600,1680);
  Object adapter=grid.getAdapter(),channel=get(f.a,"mGuidePreviewChannel"),texture=get(f.a,"mCobraPreviewTexture"),player=get(f.a,"mCobraPreviewPlayer"),epg=get(f.a,"mCobraEpg");int first=grid.getFirstVisiblePosition(),top=grid.getChildAt(0).getTop(),jobs=f.io.admitted.size();
  View focus=grid.getChildAt(0);assertTrue(focus.requestFocusFromTouch());JSONObject before=geometry(f);assertEquals(4,grid.getNumColumns());JSONArray trace=new JSONArray();
  open(f);stable(f,before,1600,1680,12,trace);assertEquals(448f,view(f,"mStage").getTranslationX(),0f);
  assertEquals(1600,view(f,"mCobraModeToolbar").getWidth());assertEquals(774,view(f,"mCobraGuideVideo").getWidth());
  call(f.a,"closeCobraExperienceDrawer");stable(f,before,1600,1680,12,trace);assertEquals(0f,view(f,"mStage").getTranslationX(),0f);
  assertSame(grid,view(f,"mCobraGuideList"));assertSame(adapter,grid.getAdapter());assertSame(channel,get(f.a,"mGuidePreviewChannel"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(epg,get(f.a,"mCobraEpg"));assertEquals(first,grid.getFirstVisiblePosition());assertEquals(top,grid.getChildAt(0).getTop());assertEquals(jobs,f.io.admitted.size());
  // The original drawer's focus transfer is allowed; channel/scroll ownership
  // and the original focusable grid objects must survive unchanged.
  assertTrue(focus.isAttachedToWindow());write("inner-animation",new JSONObject().put("frames",trace).put("state_identity_preserved",true).put("physical_Fold","NOT_RUN").put("decoder","NOT_RUN"));
 }
 @Test public void coverAndOtherModesMatchSigned435()throws Exception{
  JSONObject results=new JSONObject();
  for(String mode:new String[]{"cards","mobile","compact","grid","focus"})for(int[] size:new int[][]{{1080,2520,480},{1600,1680,320}}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture(mode,size[0],size[1],size[2]);f.a.getWindow().setLayout(size[0],size[1]);settle(f,size[0],size[1]);String key=mode+"-"+size[0];JSONObject states=new JSONObject().put("closed",geometry(f));
   if(!mode.equals("cards") || size[0]==1080){
    open(f);settle(f,size[0],size[1]);call(f.a,"cobraRestyleGuide");settle(f,size[0],size[1]);states.put("drawer",geometry(f));call(f.a,"closeCobraExperienceDrawer");settle(f,size[0],size[1]);states.put("closed_after_drawer",geometry(f));
   }
   results.put(key,states);
  }
  if(candidate())same(new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("drawer.baseline"),"negative-controls.json")),StandardCharsets.UTF_8)),results,"Exact435 fixed-viewport front/other-mode geometry");
  write("negative-controls",results);
 }
 static void resize(CobraCardsLayoutTest.Fixture f,int w,int h,int dpi)throws Exception{
  RuntimeEnvironment.setQualifiers("w"+(w*160/dpi)+"dp-h"+(h*160/dpi)+"dp-"+(w>h?"land":"port")+"-"+dpi+"dpi");
  org.robolectric.shadows.ShadowDisplay d=Shadows.shadowOf(org.robolectric.shadows.ShadowDisplay.getDefaultDisplay());d.setDensityDpi(dpi);d.setWidth(w);d.setHeight(h);d.setRealWidth(w);d.setRealHeight(h);f.a.getWindow().setLayout(w,h);layout(f,w,h);
  // Invoke the actual Activity configuration callback, not a replacement
  // responsive algorithm. Use the REAL new window for every host traversal.
  f.a.onConfigurationChanged(new Configuration(f.a.getResources().getConfiguration()));settle(f,w,h);
 }
 @Test public void drawerOpenFoldAndRotationUseRealViewport()throws Exception{
  CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1080,2520,480);f.a.getWindow().setLayout(1080,2520);settle(f,1080,2520);f.player(true);open(f);settle(f,1080,2520);
  Object channel=get(f.a,"mGuidePreviewChannel"),texture=get(f.a,"mCobraPreviewTexture"),player=get(f.a,"mCobraPreviewPlayer"),inventory=get(f.a,"mChannels"),epg=get(f.a,"mCobraEpg");JSONArray trace=new JSONArray();
  for(int[] size:new int[][]{{1600,1680,320},{1680,1600,320},{1200,1680,320},{1080,2520,480}}){
   Object grid=get(f.a,"mCobraGuideList"),theme=get(f.a,"mTheme"),ui=get(f.a,"mUi");
   resize(f,size[0],size[1],size[2]);assertSame(channel,get(f.a,"mGuidePreviewChannel"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(inventory,get(f.a,"mChannels"));assertSame(epg,get(f.a,"mCobraEpg"));assertNotNull("Retained guide drawer survives actual callback",drawer(f));
   // Signed435's unchanged callback reloads Theme/UiContract objects. Its
   // original reuse policy therefore reconstructs the guide grid. This is
   // recorded rather than mislabeled as a drawer-fix regression or hidden.
   JSONObject state=metrics(f).put("grid_identity_retained",grid==get(f.a,"mCobraGuideList")).put("theme_identity_retained",theme==get(f.a,"mTheme")).put("ui_identity_retained",ui==get(f.a,"mUi"));trace.put(state);
   if(candidate() && size[0]!=1080){assertEquals(size[0],view(f,"mCobraModeToolbar").getWidth());assertEquals(size[0]*160/size[2],get(get(f.a,"mCobraModeLayout"),"width"));JSONObject before=geometry(f);stable(f,before,size[0],size[1],4,trace);}
  }
  call(f.a,"closeCobraExperienceDrawer");settle(f,1080,2520);JSONObject closed=geometry(f);
  JSONObject result=new JSONObject().put("states",trace).put("closed_cover",closed).put("physical_Fold","NOT_RUN");write("fold-rotation",result);
  if(candidate()){
   JSONObject original=new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("drawer.baseline"),"fold-rotation.json")),StandardCharsets.UTF_8));
   // Normal cover geometry is unchanged. A journey which actually visited the
   // inner display must not inherit435's false reduced-width cover return.
   JSONObject normal=new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("drawer.baseline"),"negative-controls.json")),StandardCharsets.UTF_8)).getJSONObject("cards-1080").getJSONObject("closed");
   same(normal,closed,"Approved normal cover geometry after actual inner->cover drawer journey");
   assertEquals(2,closed.getInt("columns"));
   result.put("435_reduced_cover_return",original.getJSONObject("closed_cover"));write("fold-rotation",result);
   // A subsequent NEW cover-only drawer must not inherit inner ownership.
   open(f);settle(f,1080,2520);call(f.a,"cobraRestyleGuide");settle(f,1080,2520);
   JSONObject controls=new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("drawer.baseline"),"negative-controls.json")),StandardCharsets.UTF_8));
   same(controls.getJSONObject("cards-1080").getJSONObject("drawer"),geometry(f),"New cover-only drawer retains original435 policy");
   call(f.a,"closeCobraExperienceDrawer");settle(f,1080,2520);
  }
 }
 @Test public void rapidInterruptedDrawerAndClosingTail()throws Exception{
  assertTrue(candidate());CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1600,1680,320);f.a.getWindow().setLayout(1600,1680);settle(f,1600,1680);JSONObject before=geometry(f);JSONArray trace=new JSONArray();
  for(int i=0;i<3;i++){open(f);stable(f,before,1600,1680,i+1,trace);assertTrue(view(f,"mStage").getTranslationX()>0);call(f.a,"closeCobraExperienceDrawer");assertNull(drawer(f));assertFalse((Boolean)get(f.a,"mCobraDrawerShifted"));stable(f,before,1600,1680,2,trace);}
  stable(f,before,1600,1680,12,trace);assertEquals(0f,view(f,"mStage").getTranslationX(),0f);write("interrupted",new JSONObject().put("frames",trace));
 }
 static int[] corrected(CobraCardsLayoutTest.Fixture f,View shell)throws Exception{
  Method m=Class.forName("com.projectinfinity.kodi.CobraCardsDrawerViewport").getDeclaredMethod("location",Activity.class,View.class,int[].class);int[] xy=new int[2];m.invoke(null,f.a,shell,xy);return xy;
 }
 @Test @Config(shadows={CobraCardsLayoutTest.TerminalActions.class,InsetsInput.class})
 public void insetsAndOwnershipGuardsRemainStrict()throws Exception{
  assertTrue(candidate());CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1600,1680,320);f.a.getWindow().setLayout(1600,1680);settle(f,1600,1680);View shell=view(f,"mCobraGuideShell"),stage=view(f,"mStage");
  // Nonzero real insets remain in the ORIGINAL native arithmetic. Translation
  // never replaces or clears them. Direct guard probes cover retained overlays.
  InsetsInput.supplied=new WindowInsets(new Rect(24,32,40,48));
  assertEquals(24,shell.getRootWindowInsets().getSystemWindowInsetLeft());assertEquals(40,shell.getRootWindowInsets().getSystemWindowInsetRight());
  call(f.a,"cobraLayoutGuide");call(f.a,"cobraRestyleGuide");settle(f,1600,1680);
  assertEquals(1536,view(f,"mCobraModeToolbar").getWidth());assertEquals(24,view(f,"mCobraModeToolbar").getLeft());assertEquals(768,get(get(f.a,"mCobraModeLayout"),"width"));JSONObject insetGeometry=geometry(f);
  int[] nativeXY=new int[2];shell.getLocationInWindow(nativeXY);open(f);settle(f,1600,1680);int[] xy=corrected(f,shell);assertEquals(nativeXY[0],xy[0]);assertEquals(nativeXY[1],xy[1]);
  call(f.a,"cobraLayoutGuide");call(f.a,"cobraRestyleGuide");settle(f,1600,1680);same(insetGeometry,geometry(f),"Actual nonzero root insets survive both original sizing paths");
  int[] raw=new int[2];shell.getLocationInWindow(raw);assertEquals(448,raw[0]-xy[0]);
  set(f.a,"mCobraProSportsActive",true);assertArrayEquals(raw,corrected(f,shell));set(f.a,"mCobraProSportsActive",false);
  set(f.a,"mCobraProActive",true);assertArrayEquals(raw,corrected(f,shell));set(f.a,"mCobraProActive",false);
  FrameLayout overlay=new FrameLayout(f.a);((ViewGroup)f.a.getWindow().getDecorView()).addView(overlay,new ViewGroup.LayoutParams(1600,1680));
  for(String field:new String[]{"mPlayerOverlay","mMultiOverlay"}){set(f.a,field,overlay);assertArrayEquals(raw,corrected(f,shell));overlay.setVisibility(View.GONE);assertArrayEquals(xy,corrected(f,shell));overlay.setVisibility(View.VISIBLE);set(f.a,field,null);}
  ((ViewGroup)overlay.getParent()).removeView(overlay);assertEquals(1f,stage.getScaleX(),0f);write("ownership-insets",new JSONObject().put("raw",new JSONArray(raw)).put("layout",new JSONArray(xy)).put("guards",true).put("real_insets_ltrb",new JSONArray(new int[]{24,32,40,48})).put("geometry",geometry(f)).put("host_input","Actual WindowInsets supplied by framework test shadow; production inset arithmetic unchanged"));
 }
}
