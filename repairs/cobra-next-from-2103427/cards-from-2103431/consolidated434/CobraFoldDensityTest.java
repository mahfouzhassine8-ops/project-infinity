package com.projectinfinity.kodi;

import android.app.Application;
import android.os.Looper;
import android.view.View;
import android.widget.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;

/** Actual owner DEX native shell. Synthetic inventory; provider/decoder/shutdown not run. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 qualifiers="w358dp-h637dp-port-420dpi",instrumentedPackages={"com.projectinfinity.kodi"},
 shadows={CobraCardsLayoutTest.TerminalActions.class})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class CobraFoldDensityTest {
 static Object get(Object o,String n)throws Exception{return CobraCardsLayoutTest.get(o,n);}
 static void set(Object o,String n,Object v)throws Exception{CobraCardsLayoutTest.set(o,n,v);}
 static Object call(Object o,String n,Object...v)throws Exception{return CobraCardsLayoutTest.call(o,n,v);}
 static JSONArray reflowEvents=new JSONArray();
 static boolean candidate(){return Boolean.getBoolean("fold.candidate");}
 static Path output(){return Paths.get(System.getProperty("fold.output"));}
 static void write(String name,JSONObject value)throws Exception{Files.createDirectories(output());Files.write(output().resolve(name+".json"),(value.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}
 @Before public void frames()throws Exception{new CobraCardsLayoutTest().frames();CobraCardsLayoutTest.nativeWarmThemeSetup();}
 static void resize(CobraCardsLayoutTest.Fixture f,int w,int h,int dpi,float font)throws Exception{
  RuntimeEnvironment.setQualifiers("w"+(w*160/dpi)+"dp-h"+(h*160/dpi)+"dp-"+(w>h?"land":"port")+"-"+dpi+"dpi");
  org.robolectric.shadows.ShadowDisplay d=Shadows.shadowOf(org.robolectric.shadows.ShadowDisplay.getDefaultDisplay());d.setDensityDpi(dpi);d.setWidth(w);d.setHeight(h);d.setRealWidth(w);d.setRealHeight(h);
  f.a.getResources().getConfiguration().fontScale=font;
  // Resize the host Window as well as its Display; otherwise automatic native
  // traversals keep the old inner pixel frame while manual layout uses cover.
  f.a.getWindow().setLayout(w,h);
  call(f.a,"cobraLayoutGuide");
  Class<?> reuse=Class.forName("com.projectinfinity.kodi.CobraCardsReuse");java.lang.reflect.Method existing=reuse.getDeclaredMethod("existing",android.app.Activity.class),stamp=reuse.getDeclaredMethod("stamp",android.app.Activity.class);existing.setAccessible(true);stamp.setAccessible(true);Object state=existing.invoke(null,f.a),fresh=stamp.invoke(null,f.a);
  JSONObject why=new JSONObject().put("pending_focus",String.valueOf(get(f.a,"mCobraModePendingFocus"))).put("state_exists",state!=null);
  if(state!=null){Object old=get(state,"stamp");java.lang.reflect.Method same=old.getClass().getDeclaredMethod("sameDataForReflow",old.getClass());same.setAccessible(true);why.put("old_text",new JSONArray((String[])get(old,"text"))).put("fresh_text",new JSONArray((String[])get(fresh,"text"))).put("old_geometry",new JSONArray((int[])get(old,"geometry"))).put("fresh_geometry",new JSONArray((int[])get(fresh,"geometry"))).put("same_data_for_reflow",same.invoke(old,fresh)).put("anchor",get(state,"anchorPosition"));}
  write("reflow-admission-"+w+"-"+font,why);call(f.a,"cobraRenderGuideBrowser");
  for(int i=0;i<5;i++){
   Shadows.shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(32));
   View root=f.a.getWindow().getDecorView();root.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));root.layout(0,0,w,h);
   root.getViewTreeObserver().dispatchOnGlobalLayout();
   GridView grid=(GridView)get(f.a,"mCobraGuideList");reflowEvents.put(new JSONObject().put("iteration",i).put("first",grid.getFirstVisiblePosition()).put("top",grid.getChildCount()>0?grid.getChildAt(0).getTop():-999).put("selected",grid.getSelectedItemPosition()).put("focus",grid.findFocus()==null?"":String.valueOf(grid.findFocus().getTag())).put("columns",grid.getNumColumns()));
  }
 }
 @Test public void front433PixelGeometryAndTouchPreservation()throws Exception{
  JSONArray cases=new JSONArray();for(int[] size:new int[][]{{941,1672,420},{1080,2520,480}}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",size[0],size[1],size[2]);f.player(true);
   String name="front-"+size[0];f.image(name);JSONObject snapshot=new JSONObject().put("geometry",f.geometry()).put("shared",f.shared());
   if(candidate()){
    Path base=Paths.get(System.getProperty("fold.baseline"));JSONObject prior=new JSONObject(new String(Files.readAllBytes(base.resolve(name+".json")),StandardCharsets.UTF_8));
    assertNull("Full front433 geometry/styles",CobraCardsLayoutTest.diff(prior,snapshot,name));
    assertArrayEquals("Exact actual native front raster",Files.readAllBytes(base.resolve(name+".png")),Files.readAllBytes(output().resolve(name+".png")));
   }
   write(name,snapshot);GridView g=(GridView)get(f.a,"mCobraGuideList");assertEquals(2,g.getNumColumns());
   Object texture=get(f.a,"mCobraPreviewTexture");CobraCardsLayoutTest.ENDPOINTS.clear();
   View preview=(View)get(f.a,"mCobraPreviewHost");f.press(preview.findViewWithTag("cobra_preview_pip_small"));
   assertEquals("Existing inline PiP promotes then enters PiP",Arrays.asList("fullscreen","pip"),CobraCardsLayoutTest.ENDPOINTS);assertSame(texture,get(f.a,"mCobraPreviewTexture"));
   cases.put(new JSONObject().put("window_px",new JSONArray(size)).put("pixel_parity",candidate()).put("pip_actual_press",true));
  }write("front-preservation",new JSONObject().put("cases",cases).put("physical_Fold","NOT_RUN"));
 }
 @Test public void innerDensityAndAccessibleColumnFallback()throws Exception{
  JSONArray cases=new JSONArray();for(int[] size:new int[][]{{1600,1680,320},{1200,1680,320},{1680,1600,320}}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",size[0],size[1],size[2]);
   GridView grid=(GridView)get(f.a,"mCobraGuideList");Object model=get(f.a,"mCobraModeLayout");int width=((Number)get(model,"width")).intValue();int expected=width>=800?4:3;
   if(candidate())assertEquals(expected,grid.getNumColumns());
   JSONObject metrics=f.geometry().put("actual_columns",grid.getNumColumns()).put("visible_channels",grid.getChildCount());
   if(candidate()){
    View toolbar=(View)get(f.a,"mCobraModeToolbar"),video=(View)get(f.a,"mCobraGuideVideo"),details=(View)get(f.a,"mCobraGuideDetails"),browser=(View)get(f.a,"mCobraGuideBrowser");
    assertTrue("Compact physical header <=80dp",toolbar.getHeight()<=80*size[2]/160f);assertEquals(video.getTop(),details.getTop());assertEquals(video.getHeight(),details.getHeight());assertTrue(browser.getTop()>=video.getBottom());
    assertTrue("Multiple actual rows below compact panels",grid.getChildCount()>=grid.getNumColumns()*2);
    for(int i=0;i<grid.getChildCount();i++){
     View card=grid.getChildAt(i);View more=null;for(View v:CobraFoldCorrectiveTest.tree(card))if(String.valueOf(v.getContentDescription()).startsWith("Channel actions for "))more=v;
     assertNotNull(more);assertTrue("48dp actual inner channel menu target",more.getWidth()>=48*size[2]/160f&&more.getHeight()>=48*size[2]/160f);
     TextView now=(TextView)get(card,"now"),title=(TextView)get(card,"title");
     assertTrue(title.getTextSize()>=13*size[2]/160f);assertTrue(now.getTop()>=title.getBottom());
     assertTrue(now.getBottom()<=card.getHeight()-24*size[2]/160f);
    }
   }
   f.image("inner-"+size[0]+"x"+size[1]);cases.put(metrics);
  }
  if(candidate()){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1600,1680,320);
   for(float font:new float[]{1.5f,2f}){resize(f,1600,1680,320,font);GridView grid=(GridView)get(f.a,"mCobraGuideList");assertEquals(font==1.5f?3:2,grid.getNumColumns());cases.put(new JSONObject().put("fontScale",font).put("columns",grid.getNumColumns()).put("first_card_height_px",grid.getChildAt(0).getHeight()));}
  }
  write("inner-density",new JSONObject().put("cases",cases).put("physical_Fold","NOT_RUN"));
 }
 @Test public void foldReflowRetainsInventoryAndVisibleAnchor()throws Exception{
  assertTrue(candidate());CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1080,2520,480);GridView original=(GridView)get(f.a,"mCobraGuideList");
  original.setSelection(8);f.frames();original.scrollListBy(17);f.frames();int first=original.getFirstVisiblePosition(),top=original.getChildAt(0).getTop();Object adapter=original.getAdapter(),channel=original.getAdapter().getItem(first);set(f.a,"mGuidePreviewChannel",channel);
  View focusTarget=null;for(View v:CobraFoldCorrectiveTest.tree(original.getChildAt(0)))if(String.valueOf(v.getContentDescription()).startsWith("Channel actions for "))focusTarget=v;assertNotNull(focusTarget);
  assertTrue("Actual remote-focusable More target must take framework focus",focusTarget.requestFocusFromTouch());View focused=original.findFocus();assertNotNull(focused);String focusedClass=focused.getClass().getName();int jobs=f.io.admitted.size();Object texture=get(f.a,"mCobraPreviewTexture");
  resize(f,1600,1680,320,1f);GridView inner=(GridView)get(f.a,"mCobraGuideList");
  assertSame("No fold inventory reconstruction",original,inner);assertSame(adapter,inner.getAdapter());assertEquals(4,inner.getNumColumns());assertSame(channel,get(f.a,"mGuidePreviewChannel"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertEquals(jobs,f.io.admitted.size());
  write("fold-reflow-preassert",new JSONObject().put("first_before",first).put("top_before",top).put("first_after",inner.getFirstVisiblePosition()).put("top_after",inner.getChildCount()>0?inner.getChildAt(0).getTop():-999).put("events",reflowEvents).put("selected",inner.getSelectedItemPosition()));
  assertTrue("Same anchor belongs to first row",first>=inner.getFirstVisiblePosition()&&first<inner.getFirstVisiblePosition()+inner.getNumColumns());
  assertEquals("Pixel offset retained after reflow",top,inner.getChildAt(first-inner.getFirstVisiblePosition()).getTop());
  assertNotNull("Actual focused view survives fold",inner.findFocus());assertEquals(focusedClass,inner.findFocus().getClass().getName());assertSame(channel,inner.getAdapter().getItem(inner.getPositionForView(inner.findFocus())));
  resize(f,1080,2520,480,1f);GridView cover=(GridView)get(f.a,"mCobraGuideList");assertSame(original,cover);assertSame(adapter,cover.getAdapter());assertEquals(2,cover.getNumColumns());assertSame(channel,get(f.a,"mGuidePreviewChannel"));assertEquals(jobs,f.io.admitted.size());assertNotNull(cover.findFocus());assertEquals(focusedClass,cover.findFocus().getClass().getName());assertSame(channel,cover.getAdapter().getItem(cover.getPositionForView(cover.findFocus())));
  write("fold-reflow",new JSONObject().put("first_anchor",first).put("first_top",top).put("inventory_rebuilt",false).put("new_worker_jobs",f.io.admitted.size()-jobs).put("same_preview_texture",true).put("focused_role",focusedClass).put("focused_channel",get(channel,"id")));
 }
 @Test public void innerChannelMenuTouchAndFocusAcrossFold()throws Exception{
  assertTrue(candidate());CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",1600,1680,320);GridView grid=(GridView)get(f.a,"mCobraGuideList");View card=grid.getChildAt(1),more=null;
  for(View v:CobraFoldCorrectiveTest.tree(card))if(String.valueOf(v.getContentDescription()).startsWith("Channel actions for "))more=v;
  assertNotNull(more);assertTrue("Framework exits touch mode for remote focus",more.requestFocusFromTouch());Object expected=grid.getAdapter().getItem(1);set(f.a,"mGuidePreviewChannel",expected);assertSame(more,grid.findFocus());
  resize(f,1080,2520,480,1f);assertSame(grid,get(f.a,"mCobraGuideList"));View restored=grid.findFocus();assertNotNull("Actual More focus after fold",restored);assertEquals(more.getClass(),restored.getClass());assertSame(expected,grid.getAdapter().getItem(grid.getPositionForView(restored)));
  resize(f,1600,1680,320,1f);restored=grid.findFocus();assertNotNull(restored);assertEquals(more.getClass(),restored.getClass());assertSame(expected,grid.getAdapter().getItem(grid.getPositionForView(restored)));
  f.press(restored);f.frames();View sheet=(View)get(f.a,"mCobraActionSheet");assertNotNull("Original CHANNEL menu must open from real inner pointer",sheet);assertTrue(sheet.isAttachedToWindow());
  boolean title=false,channel=false;for(View v:CobraFoldCorrectiveTest.tree(sheet))if(v instanceof TextView){String text=((TextView)v).getText().toString();title|=text.equals("Channel actions");channel|=text.contains(String.valueOf(get(expected,"name")));}
  assertTrue(title&&channel);assertNull(get(f.a,"mPlayerOverlay"));assertTrue((Boolean)call(f.a,"closeCobraActionSheet"));
  write("inner-channel-actions",new JSONObject().put("channel",get(expected,"id")).put("actual_pointer_press",true).put("target_dp",new JSONArray(new int[]{48,48})).put("focus_role",restored.getClass().getName()).put("scope","INNER_CHANNEL_CARD_MENU; NOT_FULLSCREEN_MORE_P0"));
 }
}
