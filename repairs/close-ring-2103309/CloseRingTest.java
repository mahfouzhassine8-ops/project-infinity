package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Looper;
import android.view.View;
import android.widget.FrameLayout;
import java.io.File;
import java.io.FileOutputStream;
import java.time.Duration;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

/** Production state machine and Android views. Does not simulate native cleanup returning. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w420dp-h936dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class CloseRingTest {
  org.robolectric.android.controller.ActivityController<Activity> host;
  FrameLayout root;
  @Before public void before(){
    ReflectionHelpers.setStaticField(InfinityExitCompletion.class,"observedClosePlan",null);
    host=Robolectric.buildActivity(Activity.class).setup();root=new FrameLayout(host.get());host.get().setContentView(root);
  }
  @After public void after(){host.pause().stop().destroy();ReflectionHelpers.setStaticField(InfinityExitCompletion.class,"observedClosePlan",null);Main.MainActivity=null;}
  InfinityGlassChooser.Gear gear(boolean light,boolean cobra,int size){
    InfinityGlassChooser.Gear gear=new InfinityGlassChooser.Gear(host.get(),light,cobra);
    gear.setContentDescription(cobra?"Cobra settings and recovery":"Infinity settings and Health Center");
    root.addView(gear,new FrameLayout.LayoutParams(size,size));
    root.measure(View.MeasureSpec.makeMeasureSpec(420,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(936,View.MeasureSpec.EXACTLY));root.layout(0,0,420,936);
    gear.onWindowFocusChanged(true);poll(gear);return gear;
  }
  void poll(InfinityGlassChooser.Gear gear){ReflectionHelpers.callInstanceMethod(gear,"syncCloseProgress");}
  boolean pending(InfinityGlassChooser.Gear gear){return ReflectionHelpers.getField(gear,"closePending");}
  boolean posted(InfinityGlassChooser.Gear gear){return ReflectionHelpers.getField(gear,"progressPosted");}
  Bitmap draw(View gear){Bitmap b=Bitmap.createBitmap(gear.getWidth(),gear.getHeight(),Bitmap.Config.ARGB_8888);gear.draw(new Canvas(b));return b;}
  int blue(Bitmap b){int count=0;for(int y=0;y<b.getHeight();y++)for(int x=0;x<b.getWidth();x++){int c=b.getPixel(x,y);if(android.graphics.Color.alpha(c)>100&&android.graphics.Color.blue(c)>180&&android.graphics.Color.green(c)>90&&android.graphics.Color.red(c)<95)count++;}return count;}

  @Test public void blueRingPersistsUntilNativeCompletionAndRestoresOriginalGear(){
    for(boolean light:new boolean[]{true,false}){
      ReflectionHelpers.setStaticField(InfinityExitCompletion.class,"observedClosePlan",null);
      InfinityGlassChooser.Gear g=gear(light,false,48);Bitmap before=draw(g);assertFalse(pending(g));
      InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();assertTrue(p.requestNormal());poll(g);assertTrue(pending(g));
      Bitmap active=draw(g);assertTrue(blue(active)>blue(before)+40);assertTrue(g.getContentDescription().toString().contains("finishing"));
      assertTrue(p.stopped(false));p.destroying();poll(g);assertTrue(pending(g));
      p.completed();poll(g);assertFalse(pending(g));assertTrue(g.getContentDescription().toString().contains("ready to reopen"));
      Bitmap complete=draw(g);assertTrue(before.sameAs(complete));before.recycle();active.recycle();complete.recycle();root.removeView(g);
    }
  }
  @Test public void timeoutAndMissingOwnerNeverMeanReady(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();p.stopped(false);p.destroying();
    InfinityGlassChooser.Gear g=gear(true,false,48);Main.MainActivity=null;
    org.robolectric.shadows.ShadowSystemClock.advanceBy(Duration.ofMinutes(5));poll(g);
    assertTrue(p.stalled(android.os.SystemClock.elapsedRealtime()));assertTrue(pending(g));
    assertEquals(InfinityExitCompletion.Plan.Phase.DESTROYING,InfinityExitCompletion.closePhase());
    assertFalse(g.getContentDescription().toString().contains("ready"));
  }
  @Test public void userForceRemainsPendingUntilProcessEnds(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();assertTrue(p.force());p.destroying();p.completed();
    InfinityGlassChooser.Gear g=gear(false,false,48);assertTrue(pending(g));
    assertEquals(InfinityExitCompletion.Plan.Phase.FORCED,InfinityExitCompletion.closePhase());
  }
  @Test public void rejectedBackgroundCancelsOnlyBeforeQuit(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();assertTrue(p.cancelBeforeQuit());
    assertEquals(InfinityExitCompletion.Plan.Phase.RUNNING,InfinityExitCompletion.closePhase());
    p.requestNormal();assertFalse(p.stopped(true));assertTrue(p.stopped(false));assertFalse(p.cancelBeforeQuit());
    for(int i=0;i<20;i++){assertFalse(p.requestNormal());assertFalse(p.stopped(false));}
    assertEquals(InfinityExitCompletion.Plan.Phase.QUIT_QUEUED,InfinityExitCompletion.closePhase());
  }
  @Test public void oldOwnerCompletionCannotClearANewerClose(){
    InfinityExitCompletion.Plan old=new InfinityExitCompletion.Plan();old.requestNormal();
    InfinityExitCompletion.Plan current=new InfinityExitCompletion.Plan();current.requestNormal();current.stopped(false);
    old.destroying();old.completed();
    assertEquals(InfinityExitCompletion.Plan.Phase.QUIT_QUEUED,InfinityExitCompletion.closePhase());
    current.destroying();current.completed();
    assertEquals(InfinityExitCompletion.Plan.Phase.COMPLETE,InfinityExitCompletion.closePhase());
  }
  @Test public void cobraHasNoRingOrProgressPolling(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();InfinityGlassChooser.Gear cobra=gear(true,true,48);
    Bitmap before=draw(cobra);p.requestNormal();poll(cobra);assertFalse(pending(cobra));assertFalse(posted(cobra));
    Bitmap active=draw(cobra);assertTrue(before.sameAs(active));assertEquals("Cobra settings and recovery",cobra.getContentDescription());before.recycle();active.recycle();
  }
  @Test public void hidingDetachingAndReturningReleaseCallbacksAndRecheckCompletion(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();
    InfinityGlassChooser.Gear g=gear(false,false,48);assertTrue(posted(g));
    g.setVisibility(View.GONE);assertFalse(posted(g));p.destroying();p.completed();
    g.setVisibility(View.VISIBLE);poll(g);assertFalse(pending(g));assertTrue(posted(g));
    root.removeView(g);assertFalse(posted(g));
  }
  @Test public void livePollMovesTheArcAndClearsWithoutUserTap(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();InfinityGlassChooser.Gear g=gear(true,false,48);
    Bitmap a=draw(g);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(400));Bitmap b=draw(g);assertFalse(a.sameAs(b));
    p.destroying();p.completed();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(300));assertFalse(pending(g));a.recycle();b.recycle();
  }
  @Test public void fullChooserKeepsBothSettingsActionsAcrossWindowSizesAndPalettes()throws Exception{
    for(boolean light:new boolean[]{true,false})for(int[] size:new int[][]{{420,936},{900,768},{936,420},{360,280}}){
      int[] calls={0,0};InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();
      InfinityGlassChooser chooser=new InfinityGlassChooser(host.get(),new InfinityGlassChooser.Actions(){
        public void enter(String experience){}
        public void settings(String experience){calls["infinity".equals(experience)?0:1]++;}
        public void themes(){} public String appearance(){return light?"light":"dark";} public void appearanceChanged(){}
      });host.get().setContentView(chooser);
      chooser.measure(View.MeasureSpec.makeMeasureSpec(size[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(size[1],View.MeasureSpec.EXACTLY));chooser.layout(0,0,size[0],size[1]);
      InfinityGlassChooser.Gear infinity=(InfinityGlassChooser.Gear)chooser.findViewById(InfinityGlassChooser.SETTINGS_INFINITY);
      InfinityGlassChooser.Gear cobra=(InfinityGlassChooser.Gear)chooser.findViewById(InfinityGlassChooser.SETTINGS_COBRA);
      poll(infinity);assertTrue(pending(infinity));assertFalse(pending(cobra));assertTrue(infinity.performClick());assertTrue(cobra.performClick());assertArrayEquals(new int[]{1,1},calls);
      assertTrue(infinity.getWidth()>0);assertEquals(cobra.getWidth(),infinity.getWidth());
      File directory=new File(System.getProperty("ring.evidence"));directory.mkdirs();Bitmap image=draw(chooser);
      try(FileOutputStream out=new FileOutputStream(new File(directory,(light?"light":"dark")+"-"+size[0]+"x"+size[1]+".png"))){image.compress(Bitmap.CompressFormat.PNG,100,out);}image.recycle();
      host.get().setContentView(root);p.destroying();p.completed();
    }
  }
}
