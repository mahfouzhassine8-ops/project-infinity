package com.projectinfinity.kodi;
import android.app.Activity;
import android.graphics.*;
import android.graphics.drawable.*;
import android.view.*;
import android.widget.*;
import java.time.Duration;
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
public class WatchAmbientTest {
 ActivityController<Activity> ctl;Activity a;FrameLayout root;CobraImmersiveAmbient ambient;Bitmap sample;
 @Before public void setup(){ctl=Robolectric.buildActivity(Activity.class).setup();a=ctl.get();root=new FrameLayout(a);root.setBackgroundColor(Color.BLACK);ambient=new CobraImmersiveAmbient(a);ambient.controlsOnly(true);root.addView(ambient,new FrameLayout.LayoutParams(-1,-1));a.setContentView(root);ctl.visible();WholeUiAmbientTest.layout(root,400,800);sample=WholeUiAmbientTest.edges();ambient.testFrame(sample,new RectF(0,300,400,525),false);}
 @After public void close(){ambient.release();sample.recycle();ctl.pause().stop().destroy();}
 boolean eligible(int mode,boolean allowed,boolean multi,boolean pip,boolean bg,boolean host,boolean texture,boolean player,boolean controls){return CobraImmersiveAmbient.watchEligible(mode,allowed,true,multi,pip,bg,host,texture,player,controls);}
 Button button(int x,int y){Button b=new Button(a);b.setText("");b.setBackgroundColor(0xff071323);FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(80,60);p.leftMargin=x;p.topMargin=y;root.addView(b,p);WholeUiAmbientTest.layout(root,400,800);return b;}
 Bitmap render(){Bitmap b=Bitmap.createBitmap(400,800,Bitmap.Config.ARGB_8888);root.draw(new Canvas(b));return b;}
 @Test public void visibleSingleWatchControlsActivate(){assertTrue(eligible(2,true,false,false,false,true,true,true,true));}
 @Test public void offAndSubtleNeverActivate(){assertFalse(eligible(0,true,false,false,false,true,true,true,true));assertFalse(eligible(1,true,false,false,false,true,true,true,true));}
 @Test public void pipSuspendsWatch(){assertFalse(eligible(2,true,false,true,false,true,true,true,true));}
 @Test public void backgroundSuspendsWatch(){assertFalse(eligible(2,true,false,false,true,true,true,true,true));}
 @Test public void actualMultiViewSuspendsWatch(){assertFalse(eligible(2,true,true,false,false,true,true,true,true));}
 @Test public void hiddenControlsSuspendWatch(){assertFalse(eligible(2,true,false,false,false,true,true,true,false));}
 @Test public void invalidOrHiddenSurfaceFailsClosed(){assertFalse(eligible(2,true,false,false,false,false,true,true,true));assertFalse(eligible(2,true,false,false,false,true,false,true,true));}
 @Test public void absentPlayerOrSafePresentationDisables(){assertFalse(eligible(2,true,false,false,false,true,true,false,true));assertFalse(eligible(2,false,false,false,false,true,true,true,true));}
 @Test public void noAmbientIsDrawnOnBackgroundOrVideo(){Bitmap b=render();try{for(int[] p:new int[][]{{200,100},{200,400},{200,700},{5,799}})assertEquals(Color.BLACK,b.getPixel(p[0],p[1]));}finally{b.recycle();}}
 @Test public void fourControlsCatchSpatiallyDifferentVideoColors(){button(160,40);button(160,650);button(0,400);button(320,400);ambient.illuminateWatch(null,root);Bitmap b=render();try{int top=b.getPixel(200,70),bottom=b.getPixel(200,680),left=b.getPixel(40,430),right=b.getPixel(360,430);assertNotEquals(top,bottom);assertNotEquals(left,right);assertTrue(Color.blue(top)>Color.green(top));assertTrue(Color.green(bottom)>Color.blue(bottom));assertTrue(Color.red(left)>Color.green(left));assertTrue(Color.green(right)>Color.blue(right));save(b,"watch-controls-four-colors");}finally{b.recycle();}}
 @Test public void structuralContainersRemainUntinted(){Drawable original=root.getBackground();LinearLayout header=new LinearLayout(a);header.setBackgroundColor(Color.BLACK);root.addView(header);ambient.illuminateWatch(null,root);assertSame(original,root.getBackground());assertTrue(header.getBackground() instanceof ColorDrawable);}
 @Test public void textureAndPlayerSurfaceAreNeverWrapped(){FrameLayout host=new FrameLayout(a);host.setBackgroundColor(Color.BLACK);TextureView texture=new TextureView(a);host.addView(texture);root.addView(host);Drawable original=host.getBackground();ambient.bind(texture,host,false);ambient.illuminateWatch(null,root);assertSame(original,host.getBackground());assertNull(texture.getBackground());assertEquals(1f,texture.getAlpha(),0);}
 @Test public void submenuGlassUsesSameLivePalette(){LinearLayout panel=new LinearLayout(a);Drawable base=new CobraVisualRenderer.Glass(a,false,20,true);panel.setBackground(base);root.addView(panel,new FrameLayout.LayoutParams(200,150));ambient.illuminateWatch(null,panel);assertNotSame(base,panel.getBackground());ambient.restoreGlass();assertSame(base,panel.getBackground());}
 @Test public void focusAndPressedStateAndCallbacksArePreserved(){Button b=button(160,40);StateListDrawable base=new StateListDrawable();base.addState(new int[]{android.R.attr.state_pressed},new ColorDrawable(Color.WHITE));base.addState(new int[]{},new ColorDrawable(Color.BLACK));b.setBackground(base);final int[] clicks={0};b.setOnClickListener(v->clicks[0]++);ambient.illuminateWatch(null,root);b.setPressed(true);assertTrue(b.getBackground().isStateful());assertArrayEquals(b.getDrawableState(),base.getState());b.performClick();assertEquals(1,clicks[0]);ambient.restoreGlass();assertSame(base,b.getBackground());}
 @Test public void scrubberOnlyPlayedPartReceivesColor(){View owner=new View(a);WholeUiAmbientTest.layout(owner,400,4);Bitmap b=Bitmap.createBitmap(400,4,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);c.drawColor(Color.DKGRAY);ambient.drawWatchProgress(c,owner,.5f);try{assertNotEquals(Color.DKGRAY,b.getPixel(100,2));assertEquals(Color.DKGRAY,b.getPixel(300,2));}finally{b.recycle();}}
 @Test public void scrubberRtlKeepsUnplayedPartUnchanged(){a.getApplicationInfo().flags|=android.content.pm.ApplicationInfo.FLAG_SUPPORTS_RTL;View owner=new View(a);owner.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);WholeUiAmbientTest.layout(owner,400,4);Bitmap b=Bitmap.createBitmap(400,4,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);c.drawColor(Color.DKGRAY);ambient.drawWatchProgress(c,owner,.5f);try{assertEquals(Color.DKGRAY,b.getPixel(100,2));assertNotEquals(Color.DKGRAY,b.getPixel(300,2));}finally{b.recycle();}}
 @Test public void seekThumbRestoresExactlyWithoutChangingValue(){SeekBar seek=new SeekBar(a);seek.setMax(1000);seek.setProgress(375);GradientDrawable base=new GradientDrawable();base.setShape(GradientDrawable.OVAL);base.setColor(Color.CYAN);base.setSize(12,12);seek.setThumb(base);root.addView(seek,new FrameLayout.LayoutParams(300,28));ambient.illuminateWatch(null,root);assertNotSame(base,seek.getThumb());assertEquals(375,seek.getProgress());ambient.restoreGlass();assertSame(base,seek.getThumb());assertEquals(375,seek.getProgress());}
 @Test public void pauseRetainsPaletteAndStopsCadence()throws Exception{button(160,40);ambient.illuminateWatch(null,root);Object palette=WholeUiAmbientTest.get(ambient,"watchPalette");ambient.state(true,true);ambient.state(true,false);assertEquals(false,WholeUiAmbientTest.get(ambient,"scheduled"));assertSame(palette,WholeUiAmbientTest.get(ambient,"watchPalette"));}
 @Test public void resumeRestartsExistingCadence()throws Exception{button(160,40);ambient.illuminateWatch(null,root);ambient.state(true,false);ambient.state(true,true);assertEquals(true,WholeUiAmbientTest.get(ambient,"scheduled"));assertEquals(83L,CobraImmersiveAmbient.FRAME_INTERVAL_MS);}
 @Test public void fitBoundsExcludeLetterboxAndFillBoundsStayInsideViewport(){TextureView t=new TextureView(a);WholeUiAmbientTest.layout(t,400,800);Matrix m=new Matrix();m.setScale(1,.28125f,200,400);t.setTransform(m);RectF r=new RectF();CobraImmersiveAmbient.visiblePicture(t,r,new Matrix());assertEquals(287.5f,r.top,.001f);assertEquals(512.5f,r.bottom,.001f);m.setScale(3.55556f,1,200,400);t.setTransform(m);CobraImmersiveAmbient.visiblePicture(t,r,new Matrix());assertEquals(new RectF(0,0,400,800),r);}
 @Test public void repeatedPaintDoesNotAllocateBitmaps()throws Exception{button(160,40);ambient.illuminateWatch(null,root);Object palette=WholeUiAmbientTest.get(ambient,"watchPalette"),frame=WholeUiAmbientTest.get(ambient,"smoothed");Bitmap out=Bitmap.createBitmap(400,800,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(out);for(int i=0;i<100;i++)root.draw(c);assertSame(palette,WholeUiAmbientTest.get(ambient,"watchPalette"));assertSame(frame,WholeUiAmbientTest.get(ambient,"smoothed"));out.recycle();}
 @Test public void switchingBackToMiniRestoresWatchGlassAndUsesOneRenderer()throws Exception{Button b=button(160,40);Drawable base=b.getBackground();ambient.illuminateWatch(null,root);ambient.controlsOnly(false);assertSame(base,b.getBackground());assertNull(WholeUiAmbientTest.get(ambient,"watchPalette"));assertSame(ambient,root.getChildAt(0));}
 @Test public void suspendFadeClearsPaletteAndRestoresThumb()throws Exception{SeekBar seek=new SeekBar(a);root.addView(seek);Drawable base=seek.getThumb();ambient.illuminateWatch(null,root);ambient.state(false,false);Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(Duration.ofMillis(300));assertNull(WholeUiAmbientTest.get(ambient,"watchPalette"));assertSame(base,seek.getThumb());assertEquals(false,WholeUiAmbientTest.get(ambient,"scheduled"));}
 static final class SamplingTexture extends TextureView {
  SamplingTexture(android.content.Context c){super(c);}
  @Override public boolean isAvailable(){return true;}
  @Override public Bitmap getBitmap(Bitmap out){Canvas canvas=new Canvas(out);Paint paint=new Paint();canvas.drawColor(Color.BLACK);int w=out.getWidth(),h=out.getHeight();paint.setColor(Color.BLUE);canvas.drawRect(0,0,w,h/2,paint);paint.setColor(Color.GREEN);canvas.drawRect(0,h/2,w,h,paint);paint.setColor(Color.RED);canvas.drawRect(0,0,w/10,h,paint);paint.setColor(Color.YELLOW);canvas.drawRect(w-w/10,0,w,h,paint);return out;}
 }
 CobraImmersiveAmbient activate(Cobra2103201ScrubberTest helper)throws Exception{
  helper.before();InfinityLiveActivity activity=helper.a;
  CobraNavigationUiTest.put(activity,"mCobraEffects",new CobraPresentationEffects(activity));
  TextureView old=(TextureView)CobraNavigationUiTest.get(activity,"mPlayerTexture");FrameLayout overlay=helper.overlay;overlay.removeView(old);
  SamplingTexture texture=new SamplingTexture(activity);overlay.addView(texture,0,new FrameLayout.LayoutParams(-1,-1));CobraNavigationUiTest.put(activity,"mPlayerTexture",texture);
  helper.prefs.edit().putString(CobraPresentationEffects.AMBIENT,"immersive").commit();CobraNavigationUiTest.put(activity,"mCobraRotationResumed",true);
  helper.ui.measure(activity,412,915);CobraNavigationUiTest.call(activity,"cobraRefreshAmbient");
  return (CobraImmersiveAmbient)CobraNavigationUiTest.get(activity,"mCobraImmersiveAmbient");
 }
 @Test public void actualWatchActivityBindsFullscreenTextureAndSuspendsOnHiddenChrome()throws Exception{
  Cobra2103201ScrubberTest helper=new Cobra2103201ScrubberTest();try{
   CobraImmersiveAmbient engine=activate(helper);assertTrue(engine.isAmbientActive());assertSame(CobraNavigationUiTest.get(helper.a,"mPlayerTexture"),WholeUiAmbientTest.get(engine,"source"));assertEquals(true,WholeUiAmbientTest.get(engine,"controlsOnly"));
   ((View)CobraNavigationUiTest.get(helper.a,"mPlayerChrome")).setVisibility(View.GONE);CobraNavigationUiTest.call(helper.a,"cobraRefreshImmersiveAmbient");assertFalse(engine.isAmbientActive());assertEquals(false,WholeUiAmbientTest.get(engine,"scheduled"));
   assertEquals(0,helper.state.prepares);assertEquals(0,helper.state.mediaChanges);assertTrue(helper.state.seeks.isEmpty());
  }finally{helper.after();}
 }
 @Test public void actualWatchPauseResumePipAndBackgroundKeepPlaybackOwnership()throws Exception{
  Cobra2103201ScrubberTest helper=new Cobra2103201ScrubberTest();try{
   CobraImmersiveAmbient engine=activate(helper);Object palette=WholeUiAmbientTest.get(engine,"watchPalette");helper.state.requested=false;CobraNavigationUiTest.call(helper.a,"cobraRefreshImmersiveAmbient");assertSame(palette,WholeUiAmbientTest.get(engine,"watchPalette"));assertEquals(false,WholeUiAmbientTest.get(engine,"scheduled"));
   helper.state.requested=true;CobraNavigationUiTest.call(helper.a,"cobraRefreshImmersiveAmbient");assertEquals(true,WholeUiAmbientTest.get(engine,"scheduled"));
   CobraNavigationUiTest.put(helper.a,"mInPictureInPicture",true);CobraNavigationUiTest.call(helper.a,"cobraRefreshImmersiveAmbient");assertFalse(engine.isAmbientActive());
   CobraNavigationUiTest.put(helper.a,"mInPictureInPicture",false);CobraNavigationUiTest.put(helper.a,"mBackgroundStopped",true);CobraNavigationUiTest.call(helper.a,"cobraRefreshImmersiveAmbient");assertFalse(engine.isAmbientActive());assertEquals(false,WholeUiAmbientTest.get(engine,"scheduled"));assertEquals(0,helper.state.prepares);assertEquals(0,helper.state.mediaChanges);
  }finally{helper.after();}
 }
 @Test public void realDisplayAndMoreSubmenusUseSharedPaletteAndReuseCaptureBuffers()throws Exception{
  Cobra2103201ScrubberTest helper=new Cobra2103201ScrubberTest();try{
   CobraImmersiveAmbient engine=activate(helper);Object capture=WholeUiAmbientTest.get(engine,"watchCapture"),working=WholeUiAmbientTest.get(engine,"raw"),palette=WholeUiAmbientTest.get(engine,"watchPalette");
   java.lang.reflect.Method method=CobraImmersiveAmbient.class.getDeclaredMethod("capture");method.setAccessible(true);for(int i=0;i<30;i++)assertEquals(true,method.invoke(engine));
   assertSame(capture,WholeUiAmbientTest.get(engine,"watchCapture"));assertSame(working,WholeUiAmbientTest.get(engine,"raw"));assertSame(palette,WholeUiAmbientTest.get(engine,"watchPalette"));
   for(String menu:new String[]{"showCobraAspectPicker","showPlayerSettingsDrawer"}){
    CobraNavigationUiTest.call(helper.a,menu);helper.ui.measure(helper.a,412,915);CobraNavigationUiTest.call(helper.a,"cobraRefreshAmbient");assertTrue(engine.isAmbientActive());assertNotNull(CobraNavigationUiTest.get(helper.a,"mCobraActionSheet"));assertTrue(((java.util.List<?>)WholeUiAmbientTest.get(engine,"glass")).size()>0);assertSame(palette,WholeUiAmbientTest.get(engine,"watchPalette"));
   }
   Bitmap rendered=Bitmap.createBitmap(412,915,Bitmap.Config.ARGB_8888);helper.overlay.draw(new Canvas(rendered));save(rendered,"actual-watch-more");rendered.recycle();assertEquals(0,helper.state.prepares);assertEquals(0,helper.state.mediaChanges);
  }finally{helper.after();}
 }
 void save(Bitmap b,String name){try{java.io.File dir=new java.io.File(System.getProperty("cobra.evidence","build/evidence"),"watch-ambient");dir.mkdirs();try(java.io.FileOutputStream out=new java.io.FileOutputStream(new java.io.File(dir,name+".png"))){b.compress(Bitmap.CompressFormat.PNG,100,out);}}catch(java.io.IOException e){throw new AssertionError(e);}}
}
