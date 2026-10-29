package com.projectinfinity.kodi;
import android.app.Application;
import android.graphics.Bitmap;
import android.graphics.drawable.BitmapDrawable;
import android.os.Looper;
import android.widget.FrameLayout;
import android.widget.ImageView;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
/** Actual entry/callback methods; recording existing executor prevents HTTP.
 * Completion is a deliberately controlled IO event, not a provider benchmark. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraLogoWorkTest {
 static Object call(Object o,String name,Object...args)throws Exception{for(Method m:o.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){m.setAccessible(true);return m.invoke(o,args);}throw new NoSuchMethodException(name);}
 static Object get(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}
 static void set(Object o,String name,Object v)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);f.set(o,v);}
 static class Recording extends AbstractExecutorService {
  final List<Runnable> jobs=new ArrayList<>();public void execute(Runnable r){jobs.add(r);}
  public boolean isShutdown(){return false;}public boolean isTerminated(){return false;}
  public void shutdown(){throw new AssertionError("not selected");}public List<Runnable> shutdownNow(){throw new AssertionError("not selected");}
  public boolean awaitTermination(long n,TimeUnit t){throw new AssertionError("not selected");}
 }
 static class Fixture {
  InfinityLiveActivity a;FrameLayout root;Recording io=new Recording();
  Fixture()throws Exception{org.robolectric.android.controller.ActivityController<InfinityLiveActivity> c=Robolectric.buildActivity(InfinityLiveActivity.class);a=c.get();a.setTheme(android.R.style.Theme_Material_NoActionBar);root=new FrameLayout(a);a.setContentView(root);set(a,"mIo",io);c.visible();Shadows.shadowOf(Looper.getMainLooper()).idle();}
  ImageView view(){ImageView v=new ImageView(a);root.addView(v,new FrameLayout.LayoutParams(32,32));return v;}
  void request(String url,ImageView v)throws Exception{call(a,"cobraSportsLoadLogo",url,v);}
  void deliver(String url,Bitmap b,ImageView v)throws Exception{call(a,"lambda$cobraSportsLoadLogo$481$com-projectinfinity-kodi-InfinityLiveActivity",url,b,v);}
  void idle(){Shadows.shadowOf(Looper.getMainLooper()).idle();}
 }
 static boolean baseline(){return Boolean.getBoolean("cobra.measure.baseline");}
 static Bitmap bitmap(ImageView v){return v.getDrawable() instanceof BitmapDrawable?((BitmapDrawable)v.getDrawable()).getBitmap():null;}
 @Test public void duplicateColdLogoRequestsUseOneExistingWorkerAndFanOut()throws Exception{
  Fixture f=new Fixture();ArrayList<ImageView> views=new ArrayList<>();String url="https://example.invalid/team.png";
  for(int i=0;i<100;i++){ImageView v=f.view();views.add(v);f.request(url,v);}f.idle();
  assertEquals(baseline()?100:1,f.io.jobs.size());Bitmap logo=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);f.deliver(url,logo,views.get(0));f.idle();
  int delivered=0;for(ImageView v:views)if(bitmap(v)==logo)delivered++;assertEquals(baseline()?1:100,delivered);
  ImageView cached=f.view();f.request(url,cached);f.idle();assertSame(logo,bitmap(cached));assertEquals(baseline()?100:1,f.io.jobs.size());
  System.out.println("COBRA_LOGO_WORK baseline="+baseline()+" cold_views=100 executor_submissions="+f.io.jobs.size()+" delivered_after_one_completion="+delivered);
 }
 @Test public void distinctLogoAdmissionIsBoundedWithoutNewExecutor()throws Exception{
  Fixture f=new Fixture();for(int i=0;i<12;i++)f.request("https://example.invalid/"+i+".png",f.view());f.idle();
  assertEquals(baseline()?12:4,f.io.jobs.size());assertSame(f.io,get(f.a,"mIo"));
 }
 @Test public void oldImageCompletionCannotOverwriteReboundLogo()throws Exception{
  Fixture f=new Fixture();ImageView v=f.view();String old="https://example.invalid/old.png",current="https://example.invalid/current.png";
  f.request(old,v);f.idle();f.request(current,v);f.idle();Bitmap a=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888),b=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888);
  f.deliver(old,a,v);f.idle();if(baseline())assertSame(a,bitmap(v));else assertNull(bitmap(v));
  f.deliver(current,b,v);f.idle();assertSame(b,bitmap(v));
  f.root.removeView(v);f.deliver(old,a,v);assertSame(b,bitmap(v));
 }
}
