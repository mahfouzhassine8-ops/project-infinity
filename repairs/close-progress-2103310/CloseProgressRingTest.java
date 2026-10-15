package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Looper;
import android.os.SystemClock;
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

/** Real production state and views; milestones are not a native timing simulation. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w420dp-h936dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public class CloseProgressRingTest {
  org.robolectric.android.controller.ActivityController<Activity> host;
  FrameLayout root;
  @Before public void before(){
    ReflectionHelpers.setStaticField(InfinityExitCompletion.class,"observedClosePlan",null);
    host=Robolectric.buildActivity(Activity.class).setup();root=new FrameLayout(host.get());host.get().setContentView(root);
  }
  @After public void after(){host.pause().stop().destroy();ReflectionHelpers.setStaticField(InfinityExitCompletion.class,"observedClosePlan",null);Main.MainActivity=null;}
  InfinityGlassChooser.Gear gear(boolean light,boolean cobra,int size){
    InfinityGlassChooser.Gear g=new InfinityGlassChooser.Gear(host.get(),light,cobra);
    g.setContentDescription(cobra?"Cobra settings and recovery":"Infinity settings and Health Center");
    root.addView(g,new FrameLayout.LayoutParams(size,size));
    root.measure(View.MeasureSpec.makeMeasureSpec(420,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(936,View.MeasureSpec.EXACTLY));root.layout(0,0,420,936);
    g.onWindowFocusChanged(true);poll(g);return g;
  }
  void poll(InfinityGlassChooser.Gear g){ReflectionHelpers.callInstanceMethod(g,"syncCloseProgress");}
  boolean pending(InfinityGlassChooser.Gear g){return ReflectionHelpers.getField(g,"closePending");}
  boolean ready(InfinityGlassChooser.Gear g){return ReflectionHelpers.getField(g,"closeReady");}
  boolean posted(InfinityGlassChooser.Gear g){return ReflectionHelpers.getField(g,"progressPosted");}
  float target(InfinityGlassChooser.Gear g){return ReflectionHelpers.getField(g,"closeTargetSweep");}
  float sweep(InfinityGlassChooser.Gear g){return ReflectionHelpers.callInstanceMethod(g,"displayedCloseSweep",ReflectionHelpers.ClassParameter.from(long.class,SystemClock.uptimeMillis()));}
  void settle(InfinityGlassChooser.Gear g){org.robolectric.shadows.ShadowSystemClock.advanceBy(Duration.ofMillis(200));poll(g);}
  Bitmap draw(View view){Bitmap b=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(b));return b;}
  int blue(Bitmap b){int count=0;for(int y=0;y<b.getHeight();y++)for(int x=0;x<b.getWidth();x++){int c=b.getPixel(x,y);if(android.graphics.Color.alpha(c)>100&&android.graphics.Color.blue(c)>180&&android.graphics.Color.green(c)>90&&android.graphics.Color.red(c)<95)count++;}return count;}
  void save(Bitmap image,String name)throws Exception{
    File dir=new File(System.getProperty("ring.evidence"));dir.mkdirs();
    try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){image.compress(Bitmap.CompressFormat.PNG,100,out);}
  }

  @Test public void completedMilestonesGrowBlueArcAndFinishInAStillFullCircle()throws Exception{
    for(boolean light:new boolean[]{true,false}){
      ReflectionHelpers.setStaticField(InfinityExitCompletion.class,"observedClosePlan",null);
      InfinityGlassChooser.Gear g=gear(light,false,48);Bitmap idle=draw(g);assertFalse(pending(g));
      InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();assertTrue(p.requestNormal());poll(g);
      assertTrue(pending(g));assertEquals(0,target(g),.001f);Bitmap waiting=draw(g);save(waiting,(light?"light":"dark")+"-stage0");
      assertTrue(p.stopped(false));poll(g);assertEquals(120,target(g),.001f);assertTrue(sweep(g)>=0&&sweep(g)<=120);settle(g);
      Bitmap stopped=draw(g);save(stopped,(light?"light":"dark")+"-stage1");assertTrue(blue(stopped)>blue(idle)+20);
      p.destroying();poll(g);assertEquals(240,target(g),.001f);assertTrue(sweep(g)>=120&&sweep(g)<=240);settle(g);
      Bitmap destroying=draw(g);save(destroying,(light?"light":"dark")+"-stage2");assertTrue(blue(destroying)>blue(stopped)+15);
      p.completed();poll(g);assertFalse(pending(g));assertTrue(ready(g));assertEquals(360,target(g),.001f);settle(g);
      Bitmap complete=draw(g);save(complete,(light?"light":"dark")+"-stage3");assertTrue(blue(complete)>blue(destroying)+15);
      assertTrue(g.getContentDescription().toString().contains("ready to reopen"));
      org.robolectric.shadows.ShadowSystemClock.advanceBy(Duration.ofSeconds(5));poll(g);Bitmap later=draw(g);assertTrue(complete.sameAs(later));
      for(Bitmap b:new Bitmap[]{idle,waiting,stopped,destroying,complete,later})b.recycle();root.removeView(g);
    }
  }
  @Test public void timeoutAndMissingOwnerHoldProgressShortOfFull(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();p.stopped(false);p.destroying();
    InfinityGlassChooser.Gear g=gear(true,false,48);settle(g);Main.MainActivity=null;
    org.robolectric.shadows.ShadowSystemClock.advanceBy(Duration.ofMinutes(5));poll(g);
    assertTrue(p.stalled(SystemClock.elapsedRealtime()));assertTrue(pending(g));assertFalse(ready(g));
    assertEquals(240,target(g),.001f);assertEquals(240,sweep(g),.001f);assertFalse(g.getContentDescription().toString().contains("ready"));
  }
  @Test public void userForceHoldsLastConfirmedStageAndNeverMeansCompleted(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();p.stopped(false);
    InfinityGlassChooser.Gear g=gear(false,false,48);settle(g);assertEquals(120,target(g),.001f);
    assertTrue(p.force());p.destroying();p.completed();poll(g);settle(g);
    assertTrue(pending(g));assertFalse(ready(g));assertEquals(120,target(g),.001f);
    assertEquals(InfinityExitCompletion.Plan.Phase.FORCED,InfinityExitCompletion.closePhase());
  }
  @Test public void cancelBeforeQuitRestoresTheNormalGear(){
    InfinityGlassChooser.Gear g=gear(true,false,48);Bitmap before=draw(g);
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();poll(g);assertTrue(pending(g));
    assertTrue(p.cancelBeforeQuit());poll(g);assertFalse(pending(g));assertFalse(ready(g));Bitmap after=draw(g);assertTrue(before.sameAs(after));
    p.requestNormal();assertFalse(p.stopped(true));assertTrue(p.stopped(false));assertFalse(p.cancelBeforeQuit());poll(g);assertEquals(120,target(g),.001f);
    before.recycle();after.recycle();
  }
  @Test public void oldOwnerCompletionCannotFillANewerClose(){
    InfinityExitCompletion.Plan old=new InfinityExitCompletion.Plan();old.requestNormal();
    InfinityExitCompletion.Plan current=new InfinityExitCompletion.Plan();current.requestNormal();current.stopped(false);
    InfinityGlassChooser.Gear g=gear(true,false,48);old.destroying();old.completed();poll(g);
    assertEquals(InfinityExitCompletion.Plan.Phase.QUIT_QUEUED,InfinityExitCompletion.closePhase());assertEquals(120,target(g),.001f);assertFalse(ready(g));
    current.destroying();current.completed();poll(g);assertTrue(ready(g));assertEquals(360,target(g),.001f);
  }
  @Test public void cobraHasNoRingOrProgressPolling(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();InfinityGlassChooser.Gear cobra=gear(true,true,48);
    Bitmap before=draw(cobra);p.requestNormal();p.stopped(false);poll(cobra);assertFalse(pending(cobra));assertFalse(posted(cobra));
    Bitmap active=draw(cobra);assertTrue(before.sameAs(active));assertEquals("Cobra settings and recovery",cobra.getContentDescription());before.recycle();active.recycle();
  }
  @Test public void hidingDetachingAndReturningReleaseCallbacksAndRecheckCompletion(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();InfinityGlassChooser.Gear g=gear(false,false,48);assertTrue(posted(g));
    g.setVisibility(View.GONE);assertFalse(posted(g));p.destroying();p.completed();g.setVisibility(View.VISIBLE);poll(g);
    assertFalse(pending(g));assertTrue(ready(g));assertEquals(360,target(g),.001f);assertTrue(posted(g));root.removeView(g);assertFalse(posted(g));
  }
  @Test public void livePollingAdvancesOnlyWhenAStageCompletes(){
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();InfinityGlassChooser.Gear g=gear(true,false,48);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(2));assertEquals(0,sweep(g),.001f);
    p.stopped(false);Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(500));assertEquals(120,sweep(g),.001f);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(2));assertEquals(120,sweep(g),.001f);
    p.destroying();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(500));assertEquals(240,sweep(g),.001f);
    p.completed();Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(500));assertFalse(pending(g));assertEquals(360,sweep(g),.001f);
  }
  @Test public void freshChooserDoesNotShowAnOldCompletedClose(){
    InfinityGlassChooser.Gear idle=gear(true,false,48);Bitmap before=draw(idle);root.removeView(idle);
    InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();p.stopped(false);p.destroying();p.completed();
    InfinityGlassChooser.Gear fresh=gear(true,false,48);assertFalse(pending(fresh));assertFalse(ready(fresh));assertEquals(0,target(fresh),.001f);
    Bitmap after=draw(fresh);assertTrue(before.sameAs(after));before.recycle();after.recycle();
  }
  @Test public void fullChooserKeepsBothSettingsActionsAcrossWindowSizesAndPalettes()throws Exception{
    for(boolean light:new boolean[]{true,false})for(int[] size:new int[][]{{420,936},{900,768},{936,420},{360,280}}){
      int[] calls={0,0};InfinityExitCompletion.Plan p=new InfinityExitCompletion.Plan();p.requestNormal();p.stopped(false);
      InfinityGlassChooser chooser=new InfinityGlassChooser(host.get(),new InfinityGlassChooser.Actions(){
        public void enter(String experience){}
        public void settings(String experience){calls["infinity".equals(experience)?0:1]++;}
        public void themes(){} public String appearance(){return light?"light":"dark";} public void appearanceChanged(){}
      });host.get().setContentView(chooser);
      chooser.measure(View.MeasureSpec.makeMeasureSpec(size[0],View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(size[1],View.MeasureSpec.EXACTLY));chooser.layout(0,0,size[0],size[1]);
      InfinityGlassChooser.Gear infinity=(InfinityGlassChooser.Gear)chooser.findViewById(InfinityGlassChooser.SETTINGS_INFINITY);
      InfinityGlassChooser.Gear cobra=(InfinityGlassChooser.Gear)chooser.findViewById(InfinityGlassChooser.SETTINGS_COBRA);
      poll(infinity);settle(infinity);assertTrue(pending(infinity));assertEquals(120,target(infinity),.001f);assertFalse(pending(cobra));
      assertTrue(infinity.performClick());assertTrue(cobra.performClick());assertArrayEquals(new int[]{1,1},calls);
      assertTrue(infinity.getWidth()>0);assertEquals(cobra.getWidth(),infinity.getWidth());
      Bitmap image=draw(chooser);save(image,(light?"light":"dark")+"-"+size[0]+"x"+size[1]);image.recycle();
      host.get().setContentView(root);p.destroying();p.completed();
    }
  }
}
