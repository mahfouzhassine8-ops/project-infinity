package com.projectinfinity.kodi;

import android.app.Application;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
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
import org.robolectric.shadows.ShadowActivity;

/** Actual signed-owner Android views, controlled player state; no decoder/device claims. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
 instrumentedPackages={"com.projectinfinity.kodi"},shadows={PlayingRowAndProViewportTest.Trace.class})
@LooperMode(LooperMode.Mode.PAUSED) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class PlayingRowAndProViewportTest {
 @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true,looseSignatures=true)
 public static class Trace extends ShadowActivity {
  @Implementation protected void cobraStartDirectPreview(Object channel,Object mode,Object muted) { requests++; }
  @Implementation protected void enterCobraPictureInPicture() { pip++; }
 }
 static int requests,pip;
 static Object get(Object a,String n)throws Exception{return CobraCardsLayoutTest.get(a,n);}
 static void put(Object a,String n,Object v)throws Exception{CobraCardsLayoutTest.set(a,n,v);}
 static Object call(Object a,String n,Object...v)throws Exception{return CobraCardsLayoutTest.call(a,n,v);}
 static void frames(){CobraActualFullscreenMoreTest.pulses(24);}
 @Before public void setup(){new CobraCardsLayoutTest().frames();requests=0;pip=0;}
 static CobraCardsLayoutTest.Fixture fixture(String mode,int w,int h,int dpi,String theme)throws Exception {
  CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture(mode,w,h,dpi);
  f.a.getWindow().setLayout(w,h);f.prefs.edit().putString("cobra_appearance_mode",theme).commit();call(f.a,"cobraRestyleGuide");frames();f.player(true);call(f.a,"cobraRefreshPlayingIndicators");frames();return f;
 }
 static GridView grid(CobraCardsLayoutTest.Fixture f)throws Exception{return (GridView)get(f.a,"mCobraGuideList");}
 static View dot(View row)throws Exception{return (View)get(row,"playing");}
 static Rect bounds(View view){Rect r=new Rect();view.getGlobalVisibleRect(r);return r;}
 static void save(String name,JSONObject data)throws Exception {java.nio.file.Path p=Paths.get(System.getProperty("cards.layout.output"),name+".json");Files.createDirectories(p.getParent());Files.write(p,(data.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));}
 static JSONObject rowState(View row)throws Exception {View d=dot(row);return new JSONObject().put("row_type",row.getClass().getSimpleName()).put("dot_type",d.getClass().getSimpleName()).put("dot_attached",d.isAttachedToWindow()).put("dot_shown",d.isShown()).put("bound",get(d,"channel")!=null).put("active",get(d,"active")).put("dot_bounds",bounds(d).toShortString());}

 @Test public void baselineCardsOmitsNativeDotMobileHasIt()throws Exception {
  JSONObject rows=new JSONObject();for(String mode:new String[]{"cards","mobile"}){CobraCardsLayoutTest.Fixture f=fixture(mode,1080,2520,480,"dark");View row=((AbsListView)get(f.a,"mCobraGuideList")).getChildAt(0),d=dot(row);assertEquals(true,call(f.a,"cobraChannelActuallyPlaying",f.channels.get(0)));rows.put(mode,rowState(row));
   if(mode.equals("cards")){assertFalse(d.isAttachedToWindow());assertNull(get(d,"channel"));}
   else {assertTrue(d.isShown());assertTrue((Boolean)get(d,"active"));assertSame(f.channels.get(0),get(d,"channel"));}
  }save("BASELINE-ROW-DOT",rows);
 }
 @Test public void baselineProInnerStarvesChannels()throws Exception {
  JSONArray cases=new JSONArray();for(int[] dim:new int[][]{{1080,2520,480},{1600,1800,240}}){CobraCardsLayoutTest.Fixture f=fixture("cards",dim[0],dim[1],dim[2],"dark");f.mode("focus");put(f.a,"mCobraProState",2);call(f.a,"cobraLayoutGuide");frames();JSONObject g=f.geometry();cases.put(g);Object layout=get(f.a,"mCobraModeLayout");int[] browser=(int[])get(layout,"browser"),video=(int[])get(layout,"video");assertTrue("Baseline vertically stacks wide inner preview",browser[1]>video[1]+video[3]);}
  save("BASELINE-PRO-GEOMETRY",new JSONObject().put("cases",cases));
 }
 static List<View> playingRows(CobraCardsLayoutTest.Fixture f)throws Exception {
  List<View> result=new ArrayList<>();AbsListView list=(AbsListView)get(f.a,"mCobraGuideList");
  for(int i=0;i<list.getChildCount();i++){View row=list.getChildAt(i);View d=dot(row);if((Boolean)get(d,"active"))result.add(row);}
  return result;
 }
 static String pixels(View view)throws Exception {
  Bitmap b=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(b));int[] a=new int[b.getWidth()*b.getHeight()];b.getPixels(a,0,b.getWidth(),0,0,b.getWidth(),b.getHeight());java.nio.ByteBuffer raw=java.nio.ByteBuffer.allocate(a.length*4);for(int c:a)raw.putInt(c);b.recycle();return CobraCardsLayoutTest.hash(raw.array());
 }
 static void image(View view,String name)throws Exception {
  assertTrue(view.getWidth()>0 && view.getHeight()>0);Bitmap b=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(b));java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,bytes));Files.write(Paths.get(System.getProperty("cards.layout.output"),name+".png"),bytes.toByteArray());b.recycle();
 }
 @Test public void cardsUsesOriginalPlayingDotAcrossThemesAndViewports()throws Exception {
  JSONArray cases=new JSONArray();for(int[] dim:new int[][]{{1080,2520,480},{1600,1800,240}})for(String theme:new String[]{"light","dark","oled"}){
   CobraCardsLayoutTest.Fixture f=fixture("cards",dim[0],dim[1],dim[2],theme);View row=grid(f).getChildAt(0),d=dot(row);
   assertEquals("CobraPlayingDot",d.getClass().getSimpleName());assertTrue(d.isShown());assertSame(f.channels.get(0),get(d,"channel"));assertEquals(1,playingRows(f).size());assertFalse(d.isClickable());assertFalse(d.isFocusable());
   Rect r=bounds(d);assertFalse(r.isEmpty());for(String field:new String[]{"category","title","now","time","progress"})assertFalse("Dot must not obscure "+field,Rect.intersects(r,bounds((View)get(row,field))));
   Set<String> samples=new HashSet<>();for(int i=0;i<12;i++){samples.add(pixels(d));Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(90));}
   assertTrue("Original dot actually changes rendered pixels across bounded frames",samples.size()>3);
   cases.put(rowState(row).put("theme",theme).put("viewport",new JSONArray(dim)).put("pulse_pixel_samples",samples.size()));
  }save("CANDIDATE-CARDS-DOT",new JSONObject().put("cases",cases));
 }
 @Test public void actualSessionOwnershipPauseRetuneAndRecycling()throws Exception {
  CobraCardsLayoutTest.Fixture f=fixture("cards",1080,2520,480,"dark");View first=grid(f).getChildAt(0),second=grid(f).getChildAt(1);Object original=get(dot(first),"channel");
  put(f.a,"mGuidePreviewChannel",f.channels.get(1));call(f.a,"cobraRefreshPlayingIndicators");frames();assertSame("Selection must not move actual-playing identity",first,playingRows(f).get(0));
  f.input.ready=false;call(f.a,"cobraRefreshPlayingIndicators");frames();assertTrue(playingRows(f).isEmpty());assertFalse(dot(first).isShown());
  f.input.ready=true;f.input.state=androidx.media3.common.Player.STATE_BUFFERING;call(f.a,"cobraRefreshPlayingIndicators");frames();assertSame(first,playingRows(f).get(0));
  put(f.binding,"channel",f.channels.get(1));call(f.a,"cobraRefreshPlayingIndicators");frames();assertSame(second,playingRows(f).get(0));assertFalse((Boolean)get(dot(first),"active"));pixels(dot(first));assertFalse("Native 180ms handoff ends when painted",dot(first).isShown());
  CobraCardsTiles.bind(f.a,(LinearLayout)second,f.channels.get(8),8);frames();assertSame(f.channels.get(8),get(dot(second),"channel"));assertFalse("Recycled nonplaying row cannot retain blue dot",(Boolean)get(dot(second),"active"));
  CobraCardsTiles.bind(f.a,(LinearLayout)second,f.channels.get(1),1);frames();assertTrue((Boolean)get(dot(second),"active"));assertSame(f.channels.get(1),get(dot(second),"channel"));
  f.input.state=androidx.media3.common.Player.STATE_ENDED;call(f.a,"cobraRefreshPlayingIndicators");frames();assertTrue(playingRows(f).isEmpty());
  assertSame(f.player,get(f.a,"mCobraPreviewPlayer"));assertEquals(0,requests);save("CANDIDATE-SESSION-OWNERSHIP",new JSONObject().put("selection_independent",true).put("pause_buffer_retune_recycle_ended",true).put("decoder","CONTROLLED_NOT_TESTED"));
 }
 @Test public void previewMenuAndSizeModesRemainWorking()throws Exception {
  JSONArray cases=new JSONArray();for(int[] dim:new int[][]{{1080,2520,480},{1600,1800,240}})for(String theme:new String[]{"light","dark"}){
   CobraCardsLayoutTest.Fixture f=fixture("cards",dim[0],dim[1],dim[2],theme);View host=(View)get(f.a,"mCobraPreviewHost");Object player=f.player,texture=get(f.a,"mCobraPreviewTexture");int selected=grid(f).getFirstVisiblePosition();
   for(int mode=0;mode<14;mode++){String key=(String)call(f.a,"cobraPreferenceKey",f.channels.get(0));Object prefs=call(f.a,"cobraReadPreferences",key);put(prefs,"aspect",mode);call(f.a,"cobraSavePreferences",f.channels.get(0),key,prefs,false);f.press(host);frames();CobraActualFullscreenMoreTest.assertSheetVisible(f,"preview-actions");assertNull(get(f.a,"mPlayerOverlay"));assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertEquals(selected,grid(f).getFirstVisiblePosition());assertEquals(1,playingRows(f).size());f.a.onBackPressed();frames();assertNull(get(f.a,"mCobraActionSheet"));cases.put(new JSONObject().put("size_mode",mode).put("theme",theme).put("viewport",new JSONArray(dim)));}
  }save("CANDIDATE-PREVIEW-MENUS",new JSONObject().put("cases",cases).put("actual_decor_touch_presses",true));
 }
 @Test public void proInnerViewportAndFrontPreservation()throws Exception {
  JSONArray results=new JSONArray();JSONArray old=new JSONObject(new String(Files.readAllBytes(Paths.get(System.getProperty("cards.layout.output"),"BASELINE-PRO-GEOMETRY.json")),StandardCharsets.UTF_8)).getJSONArray("cases");
  int index=0;for(int[] dim:new int[][]{{1080,2520,480},{1600,1800,240}}){CobraCardsLayoutTest.Fixture f=fixture("cards",dim[0],dim[1],dim[2],"dark");f.mode("focus");put(f.a,"mCobraProState",2);call(f.a,"cobraLayoutGuide");frames();JSONObject actual=f.geometry();Object layout=get(f.a,"mCobraModeLayout");int[] browser=(int[])get(layout,"browser"),video=(int[])get(layout,"video");
   if(index==0){assertNull("Exact front geometry unchanged",CobraCardsLayoutTest.diff(old.getJSONObject(index),actual,"front Pro"));}
   else {assertEquals("Existing wide arrangement aligns channel browser with preview",video[1],browser[1]);assertTrue("Inner channel browser receives most usable height",browser[3]>(int)get(layout,"height")*.7);assertTrue("Readable native channel column",browser[2]>=280);assertTrue(video[0]+video[2]<=browser[0]);assertTrue(browser[3]>old.getJSONObject(index).getJSONObject("model_dp").getJSONArray("browser").getInt(3));}
   View actualList=(View)get(f.a,"mCobraGuideList");assertTrue(actualList.isShown());Rect listRect=bounds(actualList);assertFalse(listRect.isEmpty());
   if(index==1){assertTrue("Actual visible channel list gains vertical room",listRect.height()>dim[1]*.55);image((View)get(f.a,"mCobraGuideShell"),"pro-inner-candidate");}
   actual.put("actual_list_bounds",listRect.toShortString());results.put(actual);index++;
   int[][] before=(int[][])callPro("sportsGeometry",(int)get(layout,"width"),(int)get(layout,"height"),1f,2,0f);put(f.a,"mCobraProSportsActive",true);call(f.a,"cobraAdjustProLayout",layout);for(int row=0;row<4;row++)assertArrayEquals("Pro Sports original geometry frozen",before[row],(int[])get(layout,new String[]{"toolbar","video","details","browser"}[row]));
  }save("CANDIDATE-PRO-GEOMETRY",new JSONObject().put("cases",results));
 }
 static Object callPro(String name,Object...args)throws Exception {Class<?> type=Class.forName("com.projectinfinity.kodi.CobraProUi");for(java.lang.reflect.Method m:type.getDeclaredMethods())if(m.getName().equals(name)){m.setAccessible(true);return m.invoke(null,args);}throw new NoSuchMethodException(name);}
 @Test public void resizeModeReturnAndGeometryPreservation()throws Exception {
  for(String theme:new String[]{"light","dark"}){CobraCardsLayoutTest.Fixture f=fixture("cards",1600,1800,240,theme);Object player=f.player,texture=get(f.a,"mCobraPreviewTexture"),channel=get(f.a,"mGuidePreviewChannel");JSONObject before=f.geometry();
   f.mode("mobile");call(f.a,"cobraRefreshPlayingIndicators");frames();assertEquals(1,playingRows(f).size());assertTrue(dot(playingRows(f).get(0)).isShown());f.mode("cards");call(f.a,"cobraRefreshPlayingIndicators");frames();assertEquals(1,playingRows(f).size());assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertSame(channel,get(f.a,"mGuidePreviewChannel"));assertNull("Cards geometry restored after mode round trip",CobraCardsLayoutTest.diff(before,f.geometry(),"Cards restoration"));
  }
  CobraCardsLayoutTest.Fixture f=fixture("cards",1080,2520,480,"dark");f.mode("focus");put(f.a,"mCobraProState",2);Object player=get(f.a,"mCobraPreviewPlayer"),texture=get(f.a,"mCobraPreviewTexture"),channel=get(f.a,"mGuidePreviewChannel");JSONArray transitions=new JSONArray();
  for(int[] pane:new int[][]{{1600,1800,240},{1800,1600,240},{1080,2520,480},{720,1400,320}}){
   RuntimeEnvironment.setQualifiers("w"+(pane[0]*160/pane[2])+"dp-h"+(pane[1]*160/pane[2])+"dp-"+(pane[0]>pane[1]?"land":"port")+"-"+pane[2]+"dpi");org.robolectric.shadows.ShadowDisplay d=Shadows.shadowOf(f.a.getWindowManager().getDefaultDisplay());d.setDensityDpi(pane[2]);d.setWidth(pane[0]);d.setHeight(pane[1]);d.setRealWidth(pane[0]);d.setRealHeight(pane[1]);f.a.getWindow().setLayout(pane[0],pane[1]);frames();View decor=f.a.getWindow().getDecorView();Object root=org.robolectric.util.ReflectionHelpers.callInstanceMethod(decor,"getViewRootImpl");((org.robolectric.shadows.ShadowViewRootImpl)org.robolectric.shadow.api.Shadow.extract(root)).callDispatchResized();decor.measure(View.MeasureSpec.makeMeasureSpec(pane[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(pane[1],View.MeasureSpec.EXACTLY));decor.layout(0,0,pane[0],pane[1]);call(f.a,"cobraLayoutGuide");frames();Object layout=get(f.a,"mCobraModeLayout");int w=(int)get(layout,"width"),h=(int)get(layout,"height");int[] browser=(int[])get(layout,"browser"),video=(int[])get(layout,"video");
   if(w>=700 && h>=600)assertEquals(video[1],browser[1]);else {int[][] original=(int[][])callPro("sportsGeometry",w,h,1f,2,0f);assertArrayEquals("Cover/pop-up retain exact original layout",original[3],browser);}
   assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));assertSame(channel,get(f.a,"mGuidePreviewChannel"));transitions.put(new JSONObject().put("viewport",new JSONArray(pane)).put("browser_dp",new JSONArray(browser)));
  }save("CANDIDATE-RESIZE",new JSONObject().put("transitions",transitions).put("physical_Fold","NOT_TESTED"));
 }
}
