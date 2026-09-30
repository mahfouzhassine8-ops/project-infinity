package com.projectinfinity.kodi;
import android.app.Activity;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import java.time.Duration;
import java.lang.reflect.Field;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class WholeUiAmbientTest {
 ActivityController<Activity> ctl;Activity activity;FrameLayout root;CobraImmersiveAmbient ambient;Bitmap sample;
 @Before public void setup(){ctl=Robolectric.buildActivity(Activity.class).setup();activity=ctl.get();root=new FrameLayout(activity);ambient=new CobraImmersiveAmbient(activity);ambient.testPlainRendering(true);root.addView(ambient,new FrameLayout.LayoutParams(-1,-1));activity.setContentView(root);layout(root,400,800);sample=edges();}
 @After public void cleanup(){ambient.release();sample.recycle();ctl.pause().stop().destroy();}
 static void layout(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
 static Bitmap edges(){Bitmap b=Bitmap.createBitmap(144,96,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);c.drawColor(Color.MAGENTA);Paint p=new Paint();p.setColor(Color.BLUE);c.drawRect(0,0,144,8,p);p.setColor(Color.GREEN);c.drawRect(0,88,144,96,p);p.setColor(Color.RED);c.drawRect(0,8,8,88,p);p.setColor(Color.YELLOW);c.drawRect(136,8,144,88,p);return b;}
 Bitmap field(boolean light){ambient.testFrame(sample,new RectF(120,280,280,400),light);Bitmap b=Bitmap.createBitmap(400,800,Bitmap.Config.ARGB_8888);ambient.draw(new Canvas(b));return b;}
 static Object get(Object owner,String key)throws Exception{Field f=owner.getClass().getDeclaredField(key);f.setAccessible(true);return f.get(owner);}
 boolean eligible(int mode,boolean full,boolean multi,boolean pip,boolean bg,boolean host){return CobraImmersiveAmbient.eligible(mode,true,full,multi,pip,bg,true,host,true,true);}
 @Test public void visibleEmbeddedPlayerRequired(){assertTrue(eligible(2,false,false,false,false,true));assertFalse(eligible(2,false,false,false,false,false));}
 @Test public void offDoesNotActivate(){assertFalse(eligible(0,false,false,false,false,true));}
 @Test public void subtleDoesNotActivate(){assertFalse(eligible(1,false,false,false,false,true));}
 @Test public void fourEdgesRemainSpatiallyDistinct(){Bitmap b=field(false);try{int t=b.getPixel(200,100),d=b.getPixel(200,650),l=b.getPixel(30,340),r=b.getPixel(370,340);assertTrue(Color.blue(t)>Color.red(t)+80);assertTrue(Color.green(d)>Color.blue(d)+80);assertTrue(Color.red(l)>Color.green(l)+80);assertTrue(Color.red(r)>120&&Color.green(r)>120&&Color.blue(r)<50);}finally{b.recycle();}}
 @Test public void centerMagentaDoesNotCreateFullFrameWash(){Bitmap b=field(false);try{for(int[] pt:new int[][]{{200,100},{200,650},{30,340},{370,340}}){int c=b.getPixel(pt[0],pt[1]);assertFalse("No center-derived magenta veil",Color.red(c)>150&&Color.blue(c)>150&&Color.green(c)<50);}}finally{b.recycle();}}
 @Test public void wholeUiReachIncludesFarHeaderAndBottom(){Bitmap b=field(false);try{assertTrue(Color.alpha(b.getPixel(200,20))>15);assertTrue(Color.alpha(b.getPixel(200,760))>15);}finally{b.recycle();}}
 @Test public void lightIsLowerEnergyButRetainsEdgeIdentity(){Bitmap dark=field(false),light=field(true);try{int d=dark.getPixel(200,100),l=light.getPixel(200,100);assertTrue(Color.alpha(l)<Color.alpha(d)*.5f);assertTrue(Color.alpha(l)>10);assertTrue(Color.blue(l)>Color.red(l)+80);}finally{dark.recycle();light.recycle();}}
 @Test public void lightAttenuatesBrightNeutralFrames(){assertEquals(0,Color.alpha(CobraImmersiveAmbient.lightPixel(Color.WHITE,true)));assertTrue(Color.alpha(CobraImmersiveAmbient.lightPixel(0xffffee77,true))<Color.alpha(CobraImmersiveAmbient.lightPixel(0xffffee77,false)));}
 @Test public void oledNeutralBlackHasNoHaze(){assertEquals(0,Color.alpha(CobraImmersiveAmbient.lightPixel(Color.BLACK,false)));assertEquals(0,Color.alpha(CobraImmersiveAmbient.lightPixel(0xff202020,false)));}
 @Test public void sacredVideoRectangleIsTransparentAfterBlur(){Bitmap b=field(false);try{assertEquals(0,Color.alpha(b.getPixel(200,340)));assertEquals(0,Color.alpha(b.getPixel(121,281)));assertEquals(0,Color.alpha(b.getPixel(279,399)));assertNull(ambient.getBackground());}finally{b.recycle();}}
 @Test public void playerAndSurfaceNeverReceiveIllumination(){FrameLayout host=new FrameLayout(activity);TextureView texture=new TextureView(activity);host.addView(texture);root.addView(host,new FrameLayout.LayoutParams(100,100));ambient.bind(texture,host,false);ambient.testFrame(sample,new RectF(0,0,100,100),false);ambient.illuminate(root);assertNull(host.getBackground());assertNull(texture.getBackground());assertEquals(1f,texture.getAlpha(),.001f);}
 @Test public void fullscreenDisables(){assertFalse(eligible(2,true,false,false,false,true));}
 @Test public void pipDisables(){assertFalse(eligible(2,false,false,true,false,true));}
 @Test public void backgroundDisables(){assertFalse(eligible(2,false,false,false,true,true));}
 @Test public void multiviewDisables(){assertFalse(eligible(2,false,true,false,false,true));}
 @Test public void pauseStopsCadenceAndRetainsField()throws Exception{Bitmap b=field(false);b.recycle();Object last=get(ambient,"smoothed");ambient.state(true,true);assertEquals(true,get(ambient,"scheduled"));ambient.state(true,false);assertEquals(false,get(ambient,"scheduled"));assertSame(last,get(ambient,"smoothed"));assertTrue(ambient.isAmbientActive());}
 @Test public void resumeRestartsCadence()throws Exception{Bitmap b=field(false);b.recycle();ambient.state(true,false);ambient.state(true,true);assertEquals(true,get(ambient,"scheduled"));assertEquals(83L,CobraImmersiveAmbient.FRAME_INTERVAL_MS);}
 @Test public void fadeRetainsFieldUntilCompletionAndClearsStaleFrame()throws Exception{Bitmap b=field(false);b.recycle();ambient.state(false,false);assertFalse(ambient.isAmbientActive());assertEquals(false,get(ambient,"scheduled"));assertNotNull(get(ambient,"smoothed"));Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(Duration.ofMillis(300));assertEquals(View.INVISIBLE,ambient.getVisibility());assertNull(get(ambient,"smoothed"));}
 @Test public void fiveModesShareWindowRendererAndReanchorAcrossWindowBounds()throws Exception{
   CobraNavigationUiTest helper=new CobraNavigationUiTest();helper.clock();InfinityLiveActivity a=helper.fixture(20);
   try{Object first=null;for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
     CobraNavigationUiTest.put(a,"mCobraGuideStyle",mode);CobraNavigationUiTest.call(a,"cobraShowGuideShell");
     CobraImmersiveAmbient engine=(CobraImmersiveAmbient)CobraNavigationUiTest.get(a,"mCobraImmersiveAmbient");if(first==null)first=engine;else assertSame(first,engine);
     for(int[] size:new int[][]{{412,915},{280,760},{915,412},{800,640}}){helper.measure(a,size[0],size[1]);View host=(View)CobraNavigationUiTest.get(a,"mCobraPreviewHost");engine.testFrame(sample,new RectF(0,0,20,20),false);engine.testAnchor(host);Bitmap f=Bitmap.createBitmap(engine.getWidth(),engine.getHeight(),Bitmap.Config.ARGB_8888);engine.draw(new Canvas(f));f.recycle();RectF bounds=engine.sourceBoundsForTest();assertEquals(host.getWidth(),bounds.width(),1f);assertEquals(host.getHeight(),bounds.height(),1f);assertTrue(mode,bounds.width()>1&&bounds.height()>1);}
   }}finally{helper.clean(a);}
 }
 @Test public void buffersAreReusedBetweenFrames()throws Exception{Bitmap b=field(false);b.recycle();Object raw=get(ambient,"raw"),smooth=get(ambient,"smoothed"),cache=get(ambient,"field"),array=get(ambient,"filtered");b=field(false);b.recycle();assertSame(raw,get(ambient,"raw"));assertSame(smooth,get(ambient,"smoothed"));assertSame(cache,get(ambient,"field"));assertSame(array,get(ambient,"filtered"));}
 @Test public void glassRestoresOriginalDrawableAndSelection(){View card=new View(activity);CobraVisualRenderer.Glass base=new CobraVisualRenderer.Glass(activity,true,12,false);card.setBackground(base);card.setSelected(true);root.addView(card,new FrameLayout.LayoutParams(80,80));Bitmap b=field(true);b.recycle();ambient.illuminate(root);assertNotSame(base,card.getBackground());assertTrue(card.isSelected());ambient.restoreGlass();assertSame(base,card.getBackground());assertTrue(card.isSelected());assertSame(card,base.getCallback());}
}
