package com.projectinfinity.kodi;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import java.time.Duration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

/** JVM Android lifecycle validation. Does NOT execute the ARM64 Kodi engine or OEM tasks. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class StartupLifecycleTest {
  static void idle(){Shadows.shadowOf(Looper.getMainLooper()).idle();}
  static View surface(Activity a,int w,int h){
    View v=new View(a);v.setBackgroundColor(0xff10233a);a.setContentView(v);
    v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);return v;
  }
  static Bitmap draw(View v){
    Bitmap b=Bitmap.createBitmap(v.getWidth(),v.getHeight(),Bitmap.Config.ARGB_8888);
    v.getViewTreeObserver().dispatchOnDraw();v.draw(new Canvas(b));return b;
  }

  @Test public void realActivityLivenessRejectsFinishingDestroyedAndUninitializedOwners(){
    ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();Activity a=c.get();
    assertFalse(InfinityStartupHandoff.isLive(null,true,false));
    assertFalse(InfinityStartupHandoff.isLive(a,false,false));assertFalse(InfinityStartupHandoff.isLive(a,true,true));
    assertTrue(InfinityStartupHandoff.isLive(a,true,false));
    c.pause().stop(); // Home/background remains a live owner, including background playback.
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMinutes(15));assertTrue(InfinityStartupHandoff.isLive(a,true,false));
    c.restart().start().resume();assertTrue(InfinityStartupHandoff.isLive(a,true,false));
    a.finish();assertFalse(InfinityStartupHandoff.isLive(a,true,false));c.pause().stop().destroy();
    assertFalse(InfinityStartupHandoff.isLive(a,true,false));
    ActivityController<Activity> recreated=Robolectric.buildActivity(Activity.class).setup();
    assertTrue(InfinityStartupHandoff.isLive(recreated.get(),true,false));
    assertFalse(InfinityStartupHandoff.isLive(a,true,false));recreated.pause().stop().destroy();
  }

  @Test public void actualMainAccessorRejectsConstructorOnlyAndExplicitDestroyedState(){
    Main owner=Robolectric.buildActivity(Main.class).get(); // Native onCreate deliberately not invoked on host.
    assertSame(owner,Main.MainActivity);assertNull(Main.infinityLiveActivity());
    ReflectionHelpers.setField(owner,"mInfinityLaunchReady",true);assertSame(owner,Main.infinityLiveActivity());
    ReflectionHelpers.setField(owner,"mInfinityDestroyed",true);assertNull(Main.infinityLiveActivity());Main.MainActivity=null;
  }

  @Test public void launcherFlagsCannotResetLiveMainAndDeepLinkGrantsSurvive(){
    ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();
    Intent incoming=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("content://test/movie"));
    incoming.putExtra("preserved","yes");incoming.addFlags(Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|Intent.FLAG_ACTIVITY_CLEAR_TASK|
        Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_MULTIPLE_TASK|Intent.FLAG_ACTIVITY_GRANT_READ_URI_PERMISSION);
    for(boolean live:new boolean[]{false,true}){
      Intent target=InfinityStartupHandoff.mainIntent(c.get(),incoming,live);
      assertEquals(Main.class.getName(),target.getComponent().getClassName());assertEquals(incoming.getData(),target.getData());
      assertEquals("yes",target.getStringExtra("preserved"));assertEquals(Intent.ACTION_VIEW,target.getAction());
      int f=target.getFlags();assertEquals(0,f&(Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|Intent.FLAG_ACTIVITY_CLEAR_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_MULTIPLE_TASK));
      assertTrue((f&Intent.FLAG_ACTIVITY_GRANT_READ_URI_PERMISSION)!=0);assertTrue((f&Intent.FLAG_ACTIVITY_SINGLE_TOP)!=0);
      assertEquals(live,(f&Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)!=0);
    }
    c.pause().stop().destroy();
  }

  @Test public void exitRelaunchRepeatedAcrossCoverInnerSplitFreeformHasOneDrawnHandoff(){
    for(int[] size:new int[][]{{420,936},{900,768},{360,640},{360,240}})for(int iteration=0;iteration<10;iteration++){
      ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();Activity a=c.get();
      View v=surface(a,size[0],size[1]);InfinityStartupHandoff gate=new InfinityStartupHandoff(a,v);int[] count={0};
      assertTrue(gate.enqueue(()->count[0]++));assertFalse(gate.enqueue(()->count[0]++));
      gate.resume();idle();assertEquals("No handoff before draw",0,count[0]);
      Bitmap pixels=draw(v);assertEquals(0xff10233a,pixels.getPixel(0,0));pixels.recycle();idle();
      assertEquals(1,count[0]);draw(v).recycle();idle();assertEquals(1,count[0]);
      assertFalse(gate.enqueue(()->count[0]++));gate.close();a.finish();c.pause().stop().destroy();
    }
  }

  @Test public void homeBetweenDrawAndDispatchDefersUntilNextVisibleFrameAndDestroyCancels(){
    ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();
    View v=surface(c.get(),420,936);InfinityStartupHandoff gate=new InfinityStartupHandoff(c.get(),v);int[] count={0};
    gate.resume();gate.enqueue(()->count[0]++);draw(v).recycle();gate.pause();c.pause().stop();idle();assertEquals(0,count[0]);
    Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMinutes(15));assertEquals(0,count[0]);
    c.restart().start().resume();gate.resume();draw(v).recycle();idle();assertEquals(1,count[0]);gate.close();c.pause().stop().destroy();
    ActivityController<Activity> next=Robolectric.buildActivity(Activity.class).setup();
    View v2=surface(next.get(),900,768);InfinityStartupHandoff cancelled=new InfinityStartupHandoff(next.get(),v2);
    cancelled.resume();cancelled.enqueue(()->count[0]++);draw(v2).recycle();cancelled.close();next.pause().stop().destroy();idle();assertEquals(1,count[0]);
  }

  @Test public void actualSplashCreatesContentBeforeFreshLaunchAndSuppressesDuplicateIntents(){
    Main.MainActivity=null;
    ActivityController<Splash> c=Robolectric.buildActivity(Splash.class,new Intent(Intent.ACTION_MAIN));
    Splash a=c.get();a.getSharedPreferences("infinity_experience",0).edit().putString("default","infinity").commit();
    c.create();Handler machine=ReflectionHelpers.getField(a,"mStateMachine");machine.removeCallbacksAndMessages(null);
    c.start().resume().visible();
    View frame=a.findViewById(android.R.id.content);assertNotNull(frame);assertNotNull(a.findViewById(R.id.textView1));
    frame.measure(View.MeasureSpec.makeMeasureSpec(420,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(936,View.MeasureSpec.EXACTLY));frame.layout(0,0,420,936);
    a.startXBMC();a.startXBMC();assertNull(Shadows.shadowOf(a).getNextStartedActivity());
    Bitmap pixels=draw(frame);assertNotEquals("Startup corner must not be black",0xff000000,pixels.getPixel(0,0));pixels.recycle();idle();
    Intent launched=Shadows.shadowOf(a).getNextStartedActivity();assertNotNull(launched);assertEquals(Main.class.getName(),launched.getComponent().getClassName());
    assertNull(Shadows.shadowOf(a).getNextStartedActivity());assertTrue(a.isFinishing());c.pause().stop().destroy();
  }
}
