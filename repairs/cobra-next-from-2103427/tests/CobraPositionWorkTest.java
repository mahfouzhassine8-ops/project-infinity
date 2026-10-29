package com.projectinfinity.kodi;
import android.app.Application;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import java.lang.reflect.Method;
import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;

/** Same actual Activity method and work counts on the signed baseline/candidate.
 * Host API35 measures only repeated position work, not Fold frame/CPU/battery. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraPositionWorkTest {
 @Test public void actualPositionWorkCountsAndGeometry()throws Exception{
  InfinityLiveActivity a=Robolectric.buildActivity(InfinityLiveActivity.class).get();
  class Counter extends View{int calls;Counter(){super(a);}public void setLayoutParams(ViewGroup.LayoutParams p){super.setLayoutParams(p);calls++;}}
  Method method=InfinityLiveActivity.class.getDeclaredMethod("cobraPosition",View.class,int.class,int.class,int.class,int.class);method.setAccessible(true);
  Counter v=new Counter();method.invoke(a,v,4,8,600,900);int warm=v.calls;
  long[] samples=new long[7];
  for(int sample=0;sample<samples.length;sample++){long start=System.nanoTime();for(int i=0;i<1000;i++)method.invoke(a,v,4,8,600,900);samples[sample]=System.nanoTime()-start;}
  int same=v.calls-warm;boolean baseline=Boolean.getBoolean("cobra.measure.baseline");assertEquals(baseline?7000:0,same);
  int before=v.calls;method.invoke(a,v,-4,-8,900,600);assertEquals(before+1,v.calls);
  FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)v.getLayoutParams();assertEquals(0,p.leftMargin);assertEquals(0,p.topMargin);assertEquals(900,p.width);assertEquals(600,p.height);
  java.util.Arrays.sort(samples);System.out.println("COBRA_POSITION_WORK baseline="+baseline+" repeated_calls=7000 setLayoutParams="+same+" p50_ns_per_1000="+samples[3]+" min_ns="+samples[0]+" max_ns="+samples[6]);
 }
}
