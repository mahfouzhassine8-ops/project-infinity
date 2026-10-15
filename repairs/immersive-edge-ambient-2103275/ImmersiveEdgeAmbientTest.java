package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import java.time.Duration;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowChoreographer;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class ImmersiveEdgeAmbientTest {
  CobraNavigationUiTest helper;
  @Before public void before(){helper=new CobraNavigationUiTest();helper.clock();ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));}

  static void layout(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
  static Bitmap render(View v){Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));return b;}
  static int rgbDistance(int a,int b){return Math.abs(Color.red(a)-Color.red(b))+Math.abs(Color.green(a)-Color.green(b))+Math.abs(Color.blue(a)-Color.blue(b));}

  @Test public void policyRunsOnlyForImmersiveVisibleMiniPlayer(){
    int I=CobraPresentationEffects.IMMERSIVE,S=CobraPresentationEffects.SUBTLE,O=CobraPresentationEffects.OFF;
    assertTrue(CobraImmersiveAmbient.eligible(I,true,false,false,false,false,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(S,true,false,false,false,false,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(O,true,false,false,false,false,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,false,false,false,false,false,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,true,false,false,false,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,false,true,false,false,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,false,false,true,false,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,false,false,false,true,true,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,false,false,false,false,false,true,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,false,false,false,false,true,false,true,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,false,false,false,false,true,true,false,true));
    assertFalse(CobraImmersiveAmbient.eligible(I,true,false,false,false,false,true,true,true,false));
  }

  @Test public void rendererUsesReferenceScaleCadenceAndDirectionalEdgeProjection(){
    assertEquals(144,CobraImmersiveAmbient.SAMPLE_WIDTH);
    assertEquals(83L,CobraImmersiveAmbient.FRAME_INTERVAL_MS);
    assertEquals(48,CobraImmersiveAmbient.RAY_STEPS);
    assertEquals(1.65f,CobraImmersiveAmbient.SATURATION,.001f);

    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();try{
      FrameLayout root=new FrameLayout(a);root.setBackgroundColor(Color.BLACK);CobraImmersiveAmbient ambient=new CobraImmersiveAmbient(a);ambient.testPlainRendering(true);root.addView(ambient,new FrameLayout.LayoutParams(-1,-1));a.setContentView(root);layout(root,400,800);
      Bitmap sample=Bitmap.createBitmap(144,96,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(sample);c.drawColor(0xff101010);
      Paint p=new Paint();p.setColor(Color.BLUE);c.drawRect(0,0,144,8,p);p.setColor(Color.GREEN);c.drawRect(0,88,144,96,p);p.setColor(Color.RED);c.drawRect(0,0,8,96,p);p.setColor(Color.YELLOW);c.drawRect(136,0,144,96,p);
      ambient.testFrame(sample,new RectF(120,280,280,400),false);layout(root,400,800);Bitmap field=render(root);
      int top=field.getPixel(200,190),bottom=field.getPixel(200,500),left=field.getPixel(60,340),right=field.getPixel(340,340);
      assertTrue("Top ray keeps blue edge identity",Color.blue(top)>Color.red(top)+20);
      assertTrue("Bottom ray keeps green edge identity",Color.green(bottom)>Color.red(bottom)+20);
      assertTrue("Left ray keeps red edge identity",Color.red(left)>Color.green(left)+20);
      assertTrue("Right ray keeps yellow edge identity",Color.red(right)>100&&Color.green(right)>100&&Color.blue(right)<90);
      assertTrue(rgbDistance(top,bottom)>80);assertTrue(rgbDistance(left,right)>80);
      field.recycle();sample.recycle();ambient.release();
    }finally{ctl.pause().stop().destroy();}
  }

  @Test public void oneSharedAmbientViewLivesBehindMiniPlayerAcrossAllFiveCobraModes()throws Exception{
    InfinityLiveActivity a=helper.fixture(20);try{
      Object first=null;
      for(String mode:new String[]{"mobile","grid","compact","cards","focus"}){
        CobraNavigationUiTest.put(a,"mCobraGuideStyle",mode);CobraNavigationUiTest.call(a,"cobraShowGuideShell");helper.measure(a,412,915);
        View shell=(View)CobraNavigationUiTest.get(a,"mCobraGuideShell");View ambient=shell.findViewWithTag("cobra_immersive_edge_ambient");assertNotNull(mode,ambient);
        if(first==null)first=ambient;else assertSame("All Cobra modes share one renderer",first,ambient);
        assertEquals("Ambient must remain behind mini-player",0,((ViewGroup)shell).indexOfChild(ambient));
        View preview=(View)CobraNavigationUiTest.get(a,"mCobraPreviewHost");assertTrue(((ViewGroup)shell).indexOfChild(preview)>((ViewGroup)shell).indexOfChild(ambient));
      }
    }finally{helper.clean(a);}
  }

  @Test public void visualThemeTreeCannotRestyleOrCoverTheAmbientRenderer(){
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();try{
      CobraVisualRenderer.loading.set(true);CobraVisualRenderer.active=CobraVisualTheme.builtin();CobraVisualRenderer renderer=new CobraVisualRenderer(a).mode("oled");CobraImmersiveAmbient ambient=new CobraImmersiveAmbient(a);assertNull(ambient.getBackground());renderer.paint(ambient,"guide.shell/ambient");renderer.tree(ambient,"guide.shell");assertNull(ambient.getBackground());ambient.release();
    }finally{ctl.pause().stop().destroy();CobraVisualRenderer.active=CobraVisualTheme.builtin();}
  }

  @Test public void inactiveRendererCancelsSamplingAndFadesWithoutTouchingVideo(){
    ActivityController<Activity> ctl=Robolectric.buildActivity(Activity.class).setup();Activity a=ctl.get();try{
      FrameLayout root=new FrameLayout(a);CobraImmersiveAmbient ambient=new CobraImmersiveAmbient(a);root.addView(ambient,new FrameLayout.LayoutParams(-1,-1));a.setContentView(root);layout(root,412,915);
      Bitmap sample=Bitmap.createBitmap(144,96,Bitmap.Config.ARGB_8888);sample.eraseColor(0xff2080ff);ambient.testPlainRendering(true);ambient.testFrame(sample,new RectF(80,120,332,300),false);assertTrue(ambient.isAmbientActive());assertEquals(0,ambient.captureCount());
      ambient.state(false,false);Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(Duration.ofMillis(220));assertFalse(ambient.isAmbientActive());assertEquals(View.INVISIBLE,ambient.getVisibility());sample.recycle();ambient.release();
    }finally{ctl.pause().stop().destroy();}
  }
}
