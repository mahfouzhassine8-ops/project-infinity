package com.projectinfinity.kodi;
import android.graphics.*;import androidx.media3.common.*;import androidx.media3.exoplayer.ExoPlayer;import java.lang.reflect.*;import java.util.*;import android.os.*;import android.app.Application;import android.view.*;import android.widget.*;
import org.junit.*;import static org.junit.Assert.*;import org.junit.runner.RunWith;
import org.robolectric.*;import org.robolectric.annotation.*;
import org.robolectric.shadow.api.Shadow;import org.robolectric.shadows.ShadowActivity;import org.robolectric.util.ReflectionHelpers;
import org.json.*;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,qualifiers="w360dp-h840dp-port-480dpi",instrumentedPackages={"com.projectinfinity.kodi"},shadows={DisplayTest.Trace.class})
@LooperMode(LooperMode.Mode.PAUSED) @GraphicsMode(GraphicsMode.Mode.NATIVE)
public class DisplayTest {
 static int aspectCalls,channelCalls;
 static Object get(Object o,String n)throws Exception{return CobraCardsLayoutTest.get(o,n);}
 static void put(Object o,String n,Object v)throws Exception{CobraCardsLayoutTest.set(o,n,v);}
 static Object call(Object o,String n,Object...v)throws Exception{return CobraCardsLayoutTest.call(o,n,v);}
 static void frames(){CobraActualFullscreenMoreTest.pulses(20);}
 static View row(CobraCardsLayoutTest.Fixture f,String tag){return f.a.getWindow().getDecorView().findViewWithTag(tag);}
 static void pressRow(CobraCardsLayoutTest.Fixture f,String tag)throws Exception{View r=row(f,tag);assertNotNull(tag,r);ScrollView scroll=(ScrollView)row(f,"cobra_display_scroll");if(scroll!=null){Rect box=new Rect();r.getDrawingRect(box);scroll.offsetDescendantRectToMyCoords(r,box);scroll.scrollBy(0,box.top-scroll.getScrollY());frames();}f.press(r);frames();}
 static void open(CobraCardsLayoutTest.Fixture f)throws Exception{View chrome=(View)get(f.a,"mPlayerChrome");if(chrome.getAlpha()<.9f)call(f.a,"showCobraPlayerChrome");f.press(CobraActualFullscreenMoreTest.icon(chrome,"aspect"));frames();CobraActualFullscreenMoreTest.assertSheetVisible(f,"channel-aspect");}
 @Implements(value=InfinityLiveActivity.class,isInAndroidSdk=false,callThroughByDefault=true)
 public static class Trace extends ShadowActivity {
  @RealObject InfinityLiveActivity owner;
  @Implementation protected void cobraPositionAnchoredSheet(FrameLayout root,LinearLayout panel,View anchor,View pane)throws Exception{
   CobraActualFullscreenMoreTest.positionCalls++;
   JSONObject row=new JSONObject().put("before",CobraActualFullscreenMoreTest.panelState(panel));
   Shadow.directlyOn(owner,InfinityLiveActivity.class,"cobraPositionAnchoredSheet",ReflectionHelpers.ClassParameter.from(FrameLayout.class,root),ReflectionHelpers.ClassParameter.from(LinearLayout.class,panel),ReflectionHelpers.ClassParameter.from(View.class,anchor),ReflectionHelpers.ClassParameter.from(View.class,pane));
   row.put("after",CobraActualFullscreenMoreTest.panelState(panel));if(CobraActualFullscreenMoreTest.positionTrace.length()<80)CobraActualFullscreenMoreTest.positionTrace.put(row);
  }
  @Implementation protected void showCobraAspectPicker(){aspectCalls++;Shadow.directlyOn(owner,InfinityLiveActivity.class,"showCobraAspectPicker");}
 }
 @Before public void setup(){new CobraCardsLayoutTest().frames();aspectCalls=0;channelCalls=0;}
 @Test public void fullscreenDisplayRealPress()throws Exception{
  CobraCardsLayoutTest.Fixture f=CobraActualFullscreenMoreTest.fixture();CobraActualFullscreenMoreTest.actualPreviewPress(f);
  View root=(View)CobraCardsLayoutTest.get(f.a,"mPlayerChrome");
  View display=CobraActualFullscreenMoreTest.icon(root,"aspect");
  f.press(display);CobraActualFullscreenMoreTest.pulses(20);
  CobraActualFullscreenMoreTest.save("DISPLAY-REAL-PRESS",CobraActualFullscreenMoreTest.report(f).put("aspect_callbacks",aspectCalls));
  assertEquals(1,aspectCalls);if(Boolean.getBoolean("display.baseline")){assertEquals("channel-aspect",get(f.a,"mCobraSheetKind"));assertEquals("Reproduced hidden original panel",0f,((View)get(f.a,"mCobraSheetPanel")).getAlpha(),0f);return;}CobraActualFullscreenMoreTest.assertSheetVisible(f,"channel-aspect");
  Object texture=get(f.a,"mPlayerTexture");f.a.onBackPressed();frames();assertNull(get(f.a,"mCobraActionSheet"));open(f);assertEquals(2,aspectCalls);assertSame(texture,get(f.a,"mPlayerTexture"));assertSame(f.player,get(f.a,"mPlayer"));
  View close=row(f,"cobra_display_close");assertNotNull(close);f.press(close);frames();assertNull(get(f.a,"mCobraActionSheet"));open(f);assertEquals(3,aspectCalls);
 }

 @Test public void hiddenMultiHostInnerAndNonCardsIsolation()throws Exception{
  for(int[] dim:new int[][]{{1080,2520,480},{1600,1800,240}}){
   CobraCardsLayoutTest.Fixture f=new CobraCardsLayoutTest.Fixture("cards",dim[0],dim[1],dim[2]);f.a.getWindow().setLayout(dim[0],dim[1]);frames();CobraActualFullscreenMoreTest.actualPreviewPress(f);
   FrameLayout hidden=new FrameLayout(f.a);hidden.setVisibility(View.GONE);put(f.a,"mMultiOverlay",hidden);open(f);View sheet=(View)get(f.a,"mCobraActionSheet");assertSame(get(f.a,"mPlayerOverlay"),sheet.getParent());f.a.onBackPressed();frames();
   for(String mode:new String[]{"mobile","compact","grid","focus"}){put(f.a,"mCobraGuideStyle",mode);assertNull(CobraCardsLayout.frontPlayerSheetHost(f.a,"channel-aspect"));assertTrue(CobraCardsLayout.beginFrontCardsSheetReveal(f.a,(View)get(f.a,"mCobraSheetPanel")));}
   put(f.a,"mCobraGuideStyle","cards");put(f.a,"mCobraProSportsActive",true);assertNull(CobraCardsLayout.frontPlayerSheetHost(f.a,"channel-aspect"));assertNull(CobraCardsLayout.frontPlayerSheetHost(f.a,"unrelated"));
  }
 }
 static class Video implements InvocationHandler{
  CobraCardsLayoutTest.Playback base=new CobraCardsLayoutTest.Playback();int w=1920,h=1080,prepares,releases;float par=1;
  public Object invoke(Object p,Method m,Object[] args)throws Throwable{if(m.getName().equals("getVideoSize"))return new VideoSize(w,h,0,par);if(m.getName().equals("prepare"))prepares++;if(m.getName().equals("release"))releases++;return base.invoke(p,m,args);}
 }
 Video video;TextureView texture;Object channel;
 CobraCardsLayoutTest.Fixture videoFixture()throws Exception{
  CobraCardsLayoutTest.Fixture f=CobraActualFullscreenMoreTest.fixture();f.player(true);Object old=f.player;video=new Video();f.player=Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},video);f.binding=CobraCardsLayoutTest.construct("CobraPlayerBinding",f.a,f.player,f.channels.get(0));Map bindings=(Map)get(f.a,"mCobraPlayerBindings");bindings.remove(old);bindings.put(f.player,f.binding);put(f.a,"mCobraPreviewPlayer",f.player);f.press((View)get(f.a,"mCobraPreviewHost"));frames();CobraActualFullscreenMoreTest.pressPreviewFullscreenMenu(f);assertSame(f.player,get(f.a,"mPlayer"));texture=(TextureView)get(f.a,"mPlayerTexture");channel=f.channels.get(0);assertSame(texture,get(f.binding,"texture"));return f;
 }
 void size(int w,int h){texture.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));texture.layout(0,0,w,h);}
 void mode(CobraCardsLayoutTest.Fixture f,int n)throws Exception{String key=(String)call(f.a,"cobraPreferenceKey",channel);Object prefs=call(f.a,"cobraReadPreferences",key);put(prefs,"aspect",n);call(f.a,"cobraSavePreferences",channel,key,prefs,false);call(f.a,"applyCobraAspectTransform");}
 RectF picture(){RectF r=new RectF(0,0,texture.getWidth(),texture.getHeight());texture.getTransform(new Matrix()).mapRect(r);return r;}
 static float[] expected(int w,int h,float par,int vw,int vh,int mode,float x,float y){
  float a=w*par/(float)h,v=vw/(float)vh;float sx=a>=v?1:a/v,sy=a>=v?v/a:1;
  if(mode==0||mode==1||mode==13){float fill=Math.max(1/sx,1/sy);sx*=fill;sy*=fill;}
  else if(mode==12){float low=Math.min(sx,sy),fill=Math.max(1/sx,1/sy);float cap=v>=.65f&&v<=1.35f?1.7f:2.4f;float z=low>=.78f?1:Math.min(fill,Math.min(cap,Math.max(1,.78f/low)));sx*=z;sy*=z;}
  else if(mode==2||mode==3){a=mode==2?16f/9:4f/3;sx=a>=v?1:a/v;sy=a>=v?v/a:1;}
  else if(mode>=4&&mode<=6)sx*=mode==4?1.10f:mode==5?1.25f:1.40f;
  else if(mode==7){sx*=1.24f;sy*=.84f;}
  else if(mode>=8&&mode<=10){float z=mode==8?1.25f:mode==9?1.5f:2;sx*=z;sy*=z;}
  else if(mode==11){sx*=x;sy*=y;}
  return new float[]{sx,sy};
 }
 @Test public void all14TransformsSourceParResizeLateSizeAndPip()throws Exception{
  CobraCardsLayoutTest.Fixture f=videoFixture();Object original=texture;JSONArray rows=new JSONArray();
  for(int[] pane:new int[][]{{1080,2520},{1600,1800},{1800,1600},{760,1000}}){size(pane[0],pane[1]);for(int[] src:new int[][]{{1920,1080},{1440,1080},{1080,1920},{2390,1000},{720,576}}){video.w=src[0];video.h=src[1];video.par=video.w==720?1.422222f:1;for(int n=0;n<14;n++){mode(f,n);float[] ex=expected(video.w,video.h,video.par,pane[0],pane[1],n,1,1);RectF r=picture();assertEquals("mode "+n,ex[0]*pane[0],r.width(),1);assertEquals("mode "+n,ex[1]*pane[1],r.height(),1);assertEquals(pane[0]/2f,r.centerX(),1);assertEquals(pane[1]/2f,r.centerY(),1);rows.put(new JSONObject().put("mode",n).put("label",call(f.a,"cobraAspectLabel",n)).put("source",new JSONArray(new int[]{video.w,video.h})).put("pixel_aspect",video.par).put("viewport",new JSONArray(pane)).put("bounds",new JSONArray(new float[]{r.left,r.top,r.right,r.bottom})));}}
   mode(f,10);RectF zoom=picture();put(f.a,"mInPictureInPicture",true);call(f.a,"applyCobraAspectTransform");RectF safe=picture();assertTrue(safe.width()<=pane[0]+1&&safe.height()<=pane[1]+1);put(f.a,"mInPictureInPicture",false);call(f.a,"applyCobraAspectTransform");assertEquals(zoom,picture());
  }
  RectF known=picture();video.w=video.h=0;call(f.a,"applyCobraAspectTransform");assertEquals(known,picture());video.w=1440;video.h=1080;video.par=1;call(f.a,"applyCobraAspectTransform");assertNotEquals(known,picture());assertSame(original,get(f.a,"mPlayerTexture"));assertSame(f.player,get(f.a,"mPlayer"));assertEquals(0,video.prepares);assertEquals(0,video.releases);assertEquals(280,rows.length());CobraActualFullscreenMoreTest.save("ALL-MODES-GEOMETRY",new JSONObject().put("measurements",rows).put("physical_Fold","NOT_TESTED"));
 }
 @Test public void everyModeRealSelectionAndPreferenceInheritance()throws Exception{
  CobraCardsLayoutTest.Fixture f=videoFixture();int[] ids={12,13,-1,0,1,2,3,4,5,6,7,8,9,10,11};JSONArray options=new JSONArray();
  for(int id:ids){open(f);pressRow(f,"cobra-channel-aspect:"+id);Object p=call(f.a,"cobraReadPreferences",call(f.a,"cobraPreferenceKey",channel));assertEquals(id,get(p,"aspect"));if(id==11)assertEquals("channel-custom-aspect",get(f.a,"mCobraSheetKind"));if(get(f.a,"mCobraActionSheet")!=null){f.a.onBackPressed();frames();}open(f);assertTrue(row(f,"cobra-channel-aspect:"+id).isSelected());options.put(new JSONObject().put("id",id).put("label",call(f.a,"cobraAspectLabel",id)));f.a.onBackPressed();frames();}
  mode(f,-1);call(f.a,"cobraShowPlaybackDefaults");frames();pressRow(f,"cobra-default-aspect");pressRow(f,"cobra-default-aspect:3");assertEquals(4f/3,picture().width()/picture().height(),.001f);assertEquals(-1,get(call(f.a,"cobraReadPreferences",call(f.a,"cobraPreferenceKey",channel)),"aspect"));Object other=call(f.a,"cobraReadPreferences",call(f.a,"cobraPreferenceKey",f.channels.get(1)));assertEquals(-1,get(other,"aspect"));assertSame(f.player,get(f.a,"mPlayer"));assertEquals(0,video.prepares);assertEquals(0,video.releases);CobraActualFullscreenMoreTest.save("EXPOSED-MENU",new JSONObject().put("options",options));
 }

 @Test public void customSlidersPersistResetAndKeyboardActivation()throws Exception{
  CobraCardsLayoutTest.Fixture f=videoFixture();open(f);pressRow(f,"cobra-channel-aspect:11");CobraActualFullscreenMoreTest.assertSheetVisible(f,"channel-custom-aspect");
  for(String label:new String[]{"Channel width","Channel height"}){SeekBar bar=null;for(View v:CobraActualFullscreenMoreTest.tree(f.a.getWindow().getDecorView()))if(label.contentEquals(v.getContentDescription()==null?"":v.getContentDescription()))bar=(SeekBar)v;assertNotNull(bar);float x=bar.getWidth()-bar.getPaddingRight()-1,y=bar.getHeight()/2f;long t=SystemClock.uptimeMillis();for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_MOVE,MotionEvent.ACTION_UP}){MotionEvent e=MotionEvent.obtain(t,t+=16,action,x,y,0);assertTrue(bar.dispatchTouchEvent(e));e.recycle();}frames();Object p=call(f.a,"cobraReadPreferences",call(f.a,"cobraPreferenceKey",channel));assertEquals(1.8f,(Float)get(p,label.equals("Channel width")?"x":"y"),.02f);}
  f.a.onBackPressed();frames();open(f);pressRow(f,"cobra-channel-aspect:11");pressRow(f,"cobra-channel-custom-reset");Object p=call(f.a,"cobraReadPreferences",call(f.a,"cobraPreferenceKey",channel));assertEquals(1f,(Float)get(p,"x"),0);assertEquals(1f,(Float)get(p,"y"),0);f.a.onBackPressed();frames();
  View display=CobraActualFullscreenMoreTest.icon((View)get(f.a,"mPlayerChrome"),"aspect");assertTrue("Remote target is focusable",display.isFocusable());assertTrue(display.requestFocusFromTouch());display.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_DPAD_CENTER));display.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_UP,KeyEvent.KEYCODE_DPAD_CENTER));frames();CobraActualFullscreenMoreTest.assertSheetVisible(f,"channel-aspect");assertEquals(0,video.prepares);assertEquals(0,video.releases);
 }

 @Test public void globalDefaultsEveryModeAndGlobalCustom()throws Exception{
  CobraCardsLayoutTest.Fixture f=videoFixture();mode(f,-1);JSONArray choices=new JSONArray();
  for(int id:new int[]{12,13,0,1,2,3,4,5,6,7,8,9,10}){call(f.a,"cobraShowPlaybackDefaults");frames();pressRow(f,"cobra-default-aspect");CobraActualFullscreenMoreTest.assertSheetVisible(f,"default-aspect");pressRow(f,"cobra-default-aspect:"+id);assertEquals(id,f.prefs.getInt("cobra_player_aspect_mode",-99));assertEquals(-1,get(call(f.a,"cobraReadPreferences",call(f.a,"cobraPreferenceKey",channel)),"aspect"));choices.put(id);call(f.a,"closeCobraActionSheet");frames();}
  // VOD uses the original global Display menu/editor rather than a live override.
  Object vod=CobraCardsLayoutTest.construct("Channel","vod-only","VOD","Group","","","https://example.invalid/vod","qa",Collections.emptyMap());put(f.a,"mPlaying",vod);call(f.a,"showCobraAspectPicker");frames();CobraActualFullscreenMoreTest.assertSheetVisible(f,"aspect");
  // Global custom route is exposed as the existing Custom choice.
  View custom=null;for(View v:CobraActualFullscreenMoreTest.tree(f.a.getWindow().getDecorView()))if("cobra-player-aspect:11".equals(v.getTag()))custom=v;
  if(custom==null){CobraActualFullscreenMoreTest.save("GLOBAL-ROWS",new JSONObject().put("tree",CobraCardsLayoutTest.view((View)get(f.a,"mCobraSheetPanel"),true)));throw new AssertionError("Global custom tag not found");}
  pressRow(f,"cobra-player-aspect:11");CobraActualFullscreenMoreTest.assertSheetVisible(f,"custom-aspect");assertEquals(11,f.prefs.getInt("cobra_player_aspect_mode",-99));
  java.util.List<SeekBar> bars=new java.util.ArrayList<>();for(View v:CobraActualFullscreenMoreTest.tree((View)get(f.a,"mCobraSheetPanel")))if(v instanceof SeekBar)bars.add((SeekBar)v);assertEquals(2,bars.size());
  for(int i=0;i<bars.size();i++){SeekBar bar=bars.get(i);long t=SystemClock.uptimeMillis();for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_MOVE,MotionEvent.ACTION_UP}){MotionEvent e=MotionEvent.obtain(t,t+=16,action,bar.getWidth()-bar.getPaddingRight()-1,bar.getHeight()/2f,0);assertTrue(bar.dispatchTouchEvent(e));e.recycle();}frames();assertEquals(1.8f,f.prefs.getFloat(i==0?"cobra_custom_aspect_x":"cobra_custom_aspect_y",-99),.02f);}
  call(f.a,"closeCobraActionSheet");call(f.a,"showCobraCustomAspectEditor");frames();for(View v:CobraActualFullscreenMoreTest.tree((View)get(f.a,"mCobraSheetPanel")))if(v instanceof SeekBar)assertEquals(125,((SeekBar)v).getProgress());
  CobraActualFullscreenMoreTest.save("GLOBAL-MODES",new JSONObject().put("ids",choices));assertEquals(0,video.prepares);assertEquals(0,video.releases);
 }

 @Test public void actualWindowResizeMenuAndPlayerIdentity()throws Exception{
  CobraCardsLayoutTest.Fixture f=videoFixture();Object original=texture;JSONArray observations=new JSONArray();mode(f,12);
  for(int[] pane:new int[][]{{1080,2520},{1600,1800},{1800,1600},{760,1000}}){
   RuntimeEnvironment.setQualifiers("w"+pane[0]+"dp-h"+pane[1]+"dp-"+(pane[0]>pane[1]?"land":"port")+"-mdpi");org.robolectric.shadows.ShadowDisplay d=Shadows.shadowOf(f.a.getWindowManager().getDefaultDisplay());d.setDensityDpi(160);d.setWidth(pane[0]);d.setHeight(pane[1]);d.setRealWidth(pane[0]);d.setRealHeight(pane[1]);f.a.getWindow().setLayout(pane[0],pane[1]);frames();View decor=f.a.getWindow().getDecorView();Object root=ReflectionHelpers.callInstanceMethod(decor,"getViewRootImpl");((org.robolectric.shadows.ShadowViewRootImpl)Shadow.extract(root)).callDispatchResized();decor.measure(View.MeasureSpec.makeMeasureSpec(pane[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(pane[1],View.MeasureSpec.EXACTLY));decor.layout(0,0,pane[0],pane[1]);call(f.a,"cobraBuildPlayerChrome");frames();assertEquals(pane[0],decor.getWidth());assertEquals(pane[1],decor.getHeight());assertSame(original,get(f.a,"mPlayerTexture"));assertSame(f.player,get(f.a,"mPlayer"));
   open(f);Rect panel=new Rect();View v=(View)get(f.a,"mCobraSheetPanel");assertTrue(v.getGlobalVisibleRect(panel));assertTrue("Panel stays in usable window",panel.left>=0&&panel.top>=0&&panel.right<=pane[0]&&panel.bottom<=pane[1]);observations.put(new JSONObject().put("viewport",new JSONArray(pane)).put("panel",new JSONArray(new int[]{panel.left,panel.top,panel.right,panel.bottom})));f.a.onBackPressed();frames();
  }assertEquals(0,video.prepares);assertEquals(0,video.releases);CobraActualFullscreenMoreTest.save("WINDOW-RESIZE",new JSONObject().put("observations",observations).put("physical_Fold","NOT_TESTED"));
 }
}
