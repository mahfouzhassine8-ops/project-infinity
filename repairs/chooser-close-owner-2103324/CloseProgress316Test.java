package com.projectinfinity.kodi;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Looper;
import android.os.SystemClock;
import android.view.View;
import android.widget.FrameLayout;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.Duration;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

/** Production file reader and rendered views; the clock drives motion, never work. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=android.app.Application.class,manifest=Config.NONE,qualifiers="w420dp-h936dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE) @LooperMode(LooperMode.Mode.PAUSED)
public final class CloseProgress316Test {
  org.robolectric.android.controller.ActivityController<Activity> host;
  FrameLayout root;File dir;
  final long began=1791268400000L,close=1791268518551L,end=1791268578922L;
  @Before public void before()throws Exception{
    ReflectionHelpers.setStaticField(InfinityKodiShutdown.class,"cached",InfinityKodiShutdown.Snapshot.empty());
    host=Robolectric.buildActivity(Activity.class).setup();host.windowFocusChanged(true);
    root=new FrameLayout(host.get());host.get().setContentView(root);
    dir=Files.createTempDirectory("close-progress-316").toFile();
  }
  @After public void after(){host.pause().stop().destroy();
    ReflectionHelpers.setStaticField(InfinityKodiShutdown.class,"cached",InfinityKodiShutdown.Snapshot.empty());
    for(File f:dir.listFiles())f.delete();dir.delete();
  }
  void state(int pid,String owner,String phase,boolean alive)throws Exception{
    JSONObject j=new JSONObject().put("schema",2).put("pid",pid).put("owner",owner).put("launch","selection")
        .put("began",began).put("close_at","RUNNING".equals(phase)?0:close).put("phase",phase).put("live",false).put("error","");
    Files.write(new File(dir,InfinityKodiShutdown.STATE).toPath(),j.toString().getBytes(StandardCharsets.UTF_8));
    refresh(alive);
  }
  void refresh(boolean alive)throws Exception{
    InfinityKodiShutdown.Snapshot next=InfinityKodiShutdown.read(dir,(pid,owner)->alive,InfinityKodiShutdown.state());
    ReflectionHelpers.setStaticField(InfinityKodiShutdown.class,"cached",next);
  }
  void receipt(int pid,long epoch)throws Exception{
    JSONObject j=new JSONObject().put("pid",pid).put("epoch_ms",epoch).put("milestone","native.CXBMCApp.Destroy.complete");
    Files.write(new File(dir,"infinity-native-cleanup.json").toPath(),j.toString().getBytes(StandardCharsets.UTF_8));
  }
  InfinityGlassChooser.Gear gear(boolean light,boolean cobra){
    InfinityGlassChooser.Gear g=new InfinityGlassChooser.Gear(host.get(),light,cobra);
    g.setContentDescription(cobra?"Cobra settings and recovery":"Infinity settings and Health Center");
    root.addView(g,new FrameLayout.LayoutParams(64,64));layout(root,420,936);poll(g);return g;
  }
  void layout(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
  void poll(InfinityGlassChooser.Gear g){ReflectionHelpers.callInstanceMethod(g,"syncCloseProgress");}
  boolean pending(InfinityGlassChooser.Gear g){return ReflectionHelpers.getField(g,"closePending");}
  boolean ready(InfinityGlassChooser.Gear g){return ReflectionHelpers.getField(g,"closeReady");}
  boolean posted(InfinityGlassChooser.Gear g){return ReflectionHelpers.getField(g,"progressPosted");}
  float sweep(InfinityGlassChooser.Gear g){return ReflectionHelpers.callInstanceMethod(g,"displayedCloseSweep",ReflectionHelpers.ClassParameter.from(long.class,SystemClock.uptimeMillis()));}
  Bitmap draw(View v){Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);v.draw(new Canvas(b));return b;}
  void advance(long ms){org.robolectric.shadows.ShadowSystemClock.advanceBy(Duration.ofMillis(ms));}

  @Test public void arcMovesThroughActualMinuteAndCompletesOnlyAfterSamePidEnds()throws Exception{
    for(boolean light:new boolean[]{true,false}){
      state(24758,"owner-24758","ANDROID_TASK_REMOVAL",true);
      InfinityGlassChooser.Gear g=gear(light,false);Bitmap first=draw(g);
      assertTrue(pending(g));assertTrue(g.getContentDescription().toString().contains("indeterminate"));
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(523));Bitmap second=draw(g);
      assertFalse("Real polling must visibly move the arc",first.sameAs(second));
      state(24758,"owner-24758","DESTROYING",true);poll(g);
      advance(end-close);poll(g);Bitmap late=draw(g);
      assertTrue(pending(g));assertFalse(ready(g));assertTrue(sweep(g)<360);
      advance(421);poll(g);Bitmap later=draw(g);assertFalse("Motion cannot freeze at native destruction",late.sameAs(later));
      receipt(24758,end);refresh(true);poll(g);assertFalse("Receipt alone must not release a live process",ready(g));
      refresh(false);poll(g);assertTrue(ready(g));assertFalse(pending(g));assertEquals(360,sweep(g),0);
      Bitmap complete=draw(g);advance(4321);poll(g);Bitmap stable=draw(g);assertTrue(complete.sameAs(stable));
      assertTrue(g.getContentDescription().toString().contains("ready to reopen"));
      for(Bitmap b:new Bitmap[]{first,second,late,later,complete,stable})b.recycle();root.removeView(g);
    }
  }
  @Test public void fiveMinutesOfWallTimeDoesNotFillAnUnfinishedClose()throws Exception{
    state(24758,"current","DESTROYING",true);InfinityGlassChooser.Gear g=gear(false,false);
    advance(300000);poll(g);assertTrue(pending(g));assertFalse(ready(g));assertTrue(sweep(g)<360);
    Bitmap a=draw(g);advance(637);poll(g);Bitmap b=draw(g);assertFalse(a.sameAs(b));a.recycle();b.recycle();
  }
  @Test public void olderPidOrReceiptCannotConfirmThisClose()throws Exception{
    state(24758,"current","DESTROYING",true);InfinityGlassChooser.Gear g=gear(true,false);
    for(long[] stale:new long[][]{{24757,end},{24758,close-1}}){
      receipt((int)stale[0],stale[1]);refresh(false);poll(g);assertFalse(ready(g));assertTrue(sweep(g)<360);
      assertTrue(g.getContentDescription().toString().contains("without confirmed cleanup"));
      refresh(true);poll(g);
    }
    receipt(24758,end);refresh(false);poll(g);assertTrue(ready(g));
    state(24759,"new-owner","DESTROYING",true);poll(g);assertTrue(pending(g));assertFalse(ready(g));assertTrue(sweep(g)<360);
  }
  @Test public void forceAndUnconfirmedDeathNeverShowASuccessRing()throws Exception{
    state(24758,"current","FORCED",true);InfinityGlassChooser.Gear g=gear(true,false);
    receipt(24758,end);refresh(false);poll(g);assertFalse(ready(g));assertFalse(pending(g));assertEquals(90,sweep(g),0);
  }
  @Test public void cancelRestoresNormalGearAndNewOwnerCannotInheritCompletion()throws Exception{
    state(24758,"current","RUNNING",true);InfinityGlassChooser.Gear g=gear(false,false);Bitmap before=draw(g);
    state(24758,"current","ANDROID_TASK_REMOVAL",true);poll(g);assertTrue(pending(g));
    state(24758,"current","RUNNING",true);poll(g);assertFalse(pending(g));assertFalse(ready(g));
    Bitmap after=draw(g);assertTrue(before.sameAs(after));before.recycle();after.recycle();
  }
  @Test public void cobraGearHasIdenticalPixelsAndNoCloseCallbacks()throws Exception{
    for(boolean light:new boolean[]{true,false}){
      InfinityGlassChooser.Gear cobra=gear(light,true);Bitmap before=draw(cobra);
      state(24758,"current","DESTROYING",true);poll(cobra);advance(65000);poll(cobra);
      assertFalse(pending(cobra));assertFalse(ready(cobra));assertFalse(posted(cobra));
      Bitmap during=draw(cobra);assertTrue(before.sameAs(during));
      receipt(24758,end);refresh(false);poll(cobra);Bitmap after=draw(cobra);assertTrue(before.sameAs(after));
      assertEquals("Cobra settings and recovery",cobra.getContentDescription());
      before.recycle();during.recycle();after.recycle();root.removeView(cobra);
    }
  }
  @Test public void hiddenDetachedAndRecreatedViewsStopCallbacksAndResumeCurrentState()throws Exception{
    state(24758,"current","DESTROYING",true);InfinityGlassChooser.Gear g=gear(false,false);assertTrue(posted(g));
    g.setVisibility(View.GONE);assertFalse(posted(g));receipt(24758,end);refresh(false);
    g.setVisibility(View.VISIBLE);poll(g);assertTrue(ready(g));root.removeView(g);assertFalse(posted(g));
    state(24759,"new-owner","DESTROYING",true);InfinityGlassChooser.Gear rotated=gear(false,false);
    assertTrue(pending(rotated));Bitmap a=draw(rotated);advance(357);poll(rotated);Bitmap b=draw(rotated);assertFalse(a.sameAs(b));
    a.recycle();b.recycle();root.removeView(rotated);assertFalse(posted(rotated));
  }
  @Test public void freshChooserDoesNotReplayOldCompletedClose()throws Exception{
    receipt(24758,end);state(24758,"current","DESTROYING",false);
    InfinityGlassChooser.Gear g=gear(true,false);assertFalse(ready(g));assertFalse(pending(g));assertEquals(0,sweep(g),0);
  }
  @Test public void reducedMotionStillWaitsForConfirmedCompletion()throws Exception{
    ReflectionHelpers.callStaticMethod(android.animation.ValueAnimator.class,"setDurationScale",ReflectionHelpers.ClassParameter.from(float.class,0f));
    try{
      state(24758,"current","DESTROYING",true);InfinityGlassChooser.Gear g=gear(true,false);
      Bitmap a=draw(g);advance(120000);poll(g);Bitmap b=draw(g);assertTrue(a.sameAs(b));assertFalse(ready(g));
      receipt(24758,end);refresh(false);poll(g);assertEquals(360,sweep(g),0);a.recycle();b.recycle();
    }finally{ReflectionHelpers.callStaticMethod(android.animation.ValueAnimator.class,"setDurationScale",ReflectionHelpers.ClassParameter.from(float.class,1f));}
  }
  @Test public void bothSettingsRemainInteractiveAcrossWindowSizesAndPalettes()throws Exception{
    for(String appearance:new String[]{"light","dark","oled"})for(int[] size:new int[][]{{420,936},{900,768},{936,420},{360,280}}){
      state(24758,"current","DESTROYING",true);final int[] calls={0,0};
      InfinityGlassChooser chooser=new InfinityGlassChooser(host.get(),new InfinityGlassChooser.Actions(){
        public void enter(String experience){} public void settings(String experience){calls["infinity".equals(experience)?0:1]++;}
        public void themes(){} public String appearance(){return appearance;} public void appearanceChanged(){}
      });host.get().setContentView(chooser);layout(chooser,size[0],size[1]);
      InfinityGlassChooser.Gear infinity=(InfinityGlassChooser.Gear)chooser.findViewById(InfinityGlassChooser.SETTINGS_INFINITY);
      InfinityGlassChooser.Gear cobra=(InfinityGlassChooser.Gear)chooser.findViewById(InfinityGlassChooser.SETTINGS_COBRA);
      poll(infinity);poll(cobra);assertTrue(pending(infinity));assertFalse(pending(cobra));assertFalse(posted(cobra));
      assertTrue(infinity.performClick());assertTrue(cobra.performClick());assertArrayEquals(new int[]{1,1},calls);
      assertTrue(infinity.getWidth()>0);assertEquals(cobra.getWidth(),infinity.getWidth());host.get().setContentView(root);
      assertFalse(posted(infinity));
    }
  }
}
