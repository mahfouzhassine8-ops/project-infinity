package com.projectinfinity.kodi;
import android.app.Activity;
import android.view.*;
import android.widget.*;
import java.lang.reflect.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,manifest=Config.NONE)
public class CobraMeasuredReflowTest {
 static Object invoke(Object o,String n)throws Exception{Method m=o.getClass().getDeclaredMethod(n);m.setAccessible(true);return m.invoke(o);}
 static void set(Object o,String n,Object v)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
 static void layout(View root,int w,int h){root.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));root.layout(0,0,w,h);}
 @Test public void shippedSizingReproducesPinnedCoverCanvas()throws Exception {
  InfinityLiveActivity activity=Robolectric.buildActivity(InfinityLiveActivity.class).get();
  FrameLayout parent=new FrameLayout(activity);FrameLayout canvas=new FrameLayout(activity);
  parent.addView(canvas,new FrameLayout.LayoutParams(-1,-1));set(activity,"mMultiOverlay",parent);set(activity,"mCobraMultiCanvas",canvas);
  layout(parent,480,1000);invoke(activity,"cobraLayoutPlayerPanels");layout(parent,480,1000);
  // Configuration callback runs before Android has measured the new window.
  invoke(activity,"cobraLayoutPlayerPanels");layout(parent,1800,1500);
  assertEquals(1800,parent.getWidth());assertEquals("shipped canvas remains cover-width",480,canvas.getWidth());
 }
 public static class OwnerActivity extends Activity implements CobraWindowReflow.Owner {
  View surface;Runnable reflow;int calls;
  public View cobraReflowSurface(){return surface;}
  public void cobraReflowMeasuredWindow(){calls++;reflow.run();}
 }
 @Test public void postMeasureObserverRepairsBothDirectionsWithoutConfiguration()throws Exception {
  InfinityLiveActivity shipped=Robolectric.buildActivity(InfinityLiveActivity.class).get();
  OwnerActivity window=Robolectric.buildActivity(OwnerActivity.class).setup().get();
  FrameLayout parent=new FrameLayout(window),canvas=new FrameLayout(window);parent.addView(canvas,new FrameLayout.LayoutParams(-1,-1));window.setContentView(parent);
  set(shipped,"mMultiOverlay",parent);set(shipped,"mCobraMultiCanvas",canvas);window.surface=parent;
  window.reflow=()->{try{invoke(shipped,"cobraLayoutPlayerPanels");}catch(Exception e){throw new RuntimeException(e);}};
  CobraWindowReflow.install(window);
  for(int[] size:new int[][]{{480,1000},{1800,1500},{1500,1800},{480,1000}}){
   layout(parent,size[0],size[1]);parent.getViewTreeObserver().dispatchOnPreDraw();layout(parent,size[0],size[1]);
   assertEquals(size[0],canvas.getWidth());assertEquals(size[1],canvas.getHeight());
  }
  assertEquals(4,window.calls);
 }

 static Object get(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
 static Object construct(Class<?> c,Object...args)throws Exception{for(Constructor<?> ctor:c.getDeclaredConstructors())if(ctor.getParameterCount()==args.length){ctor.setAccessible(true);return ctor.newInstance(args);}throw new AssertionError(c);}
 @Test public void allMultiCountsRetainOriginalPolicyAndTileIdentities()throws Exception {
  Class<?> channel=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$Channel");
  Class<?> tileClass=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$CobraVideoTile");
  Class<?> policy=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$CobraMultiLayoutPolicy");
  Method rect=policy.getDeclaredMethod("rect",int.class,int.class,int.class,int.class,int.class,boolean.class);rect.setAccessible(true);
  for(int count=2;count<=4;count++)for(boolean fill:new boolean[]{false,true})for(boolean enlarged:new boolean[]{false,true}){
   InfinityLiveActivity shipped=Robolectric.buildActivity(InfinityLiveActivity.class).get();
   OwnerActivity window=Robolectric.buildActivity(OwnerActivity.class).setup().get();
   FrameLayout parent=new FrameLayout(window),canvas=new FrameLayout(window);parent.addView(canvas,new FrameLayout.LayoutParams(-1,-1));window.setContentView(parent);
   set(shipped,"mMultiOverlay",parent);set(shipped,"mCobraMultiCanvas",canvas);
   android.content.SharedPreferences prefs=window.getSharedPreferences("matrix",0);
   Field fillKey=InfinityLiveActivity.class.getDeclaredField("COBRA_MULTI_LAYOUT_FILL");fillKey.setAccessible(true);
   prefs.edit().putBoolean((String)fillKey.get(null),fill).commit();set(shipped,"mPrefs",prefs);
   Object store=get(shipped,"mCobraTiles");java.util.Map entries=(java.util.Map)get(store,"entries");
   Object channels=Array.newInstance(channel,count);Object[] tiles=new Object[count];
   for(int i=0;i<count;i++){
    Object c=construct(channel,"id"+i,"channel"+i,"group","","","https://example.invalid/"+i,"",new java.util.HashMap());
    Array.set(channels,i,c);Object t=construct(tileClass,shipped,c);tiles[i]=t;entries.put("id"+i,t);canvas.addView((View)get(t,"view"));
   }
   set(shipped,"mMultiChannels",channels);set(shipped,"mCobraMultiEnlargedKey",enlarged?"id0":"");
   window.surface=parent;window.reflow=()->{try{invoke(shipped,"cobraLayoutPlayerPanels");}catch(Exception e){throw new RuntimeException(e);}};
   CobraWindowReflow.install(window);
   for(int[] size:new int[][]{{480,1000},{1800,1500},{1500,1800},{480,1000}}){
    layout(parent,size[0],size[1]);parent.getViewTreeObserver().dispatchOnPreDraw();layout(parent,size[0],size[1]);
    invoke(shipped,"cobraLayoutMultiTiles");layout(parent,size[0],size[1]);
    assertEquals(size[0],canvas.getWidth());assertEquals(size[1],canvas.getHeight());long area=0;
    for(int i=0;i<count;i++){
     assertSame(tiles[i],entries.get("id"+i));FrameLayout view=(FrameLayout)get(tiles[i],"view");
     int[] expected=(int[])rect.invoke(null,i,count,size[0],size[1],enlarged?0:-1,fill);
     assertArrayEquals(expected,new int[]{view.getLeft(),view.getTop(),view.getWidth(),view.getHeight()});
     TextureView texture=(TextureView)get(tiles[i],"texture");assertEquals(view.getWidth(),texture.getWidth());assertEquals(view.getHeight(),texture.getHeight());
     area+=(long)view.getWidth()*view.getHeight();
    }
    if(fill)assertEquals((long)size[0]*size[1],area);
   }
  }
 }
 @Test public void singlePlayerAndReplacementSurfaceReflowWithStableWindow()throws Exception {
  InfinityLiveActivity shipped=Robolectric.buildActivity(InfinityLiveActivity.class).get();
  OwnerActivity window=Robolectric.buildActivity(OwnerActivity.class).setup().get();
  FrameLayout parent=new FrameLayout(window);TextureView texture=new TextureView(window);parent.addView(texture,new FrameLayout.LayoutParams(-1,-1));window.setContentView(parent);
  set(shipped,"mPlayerOverlay",parent);set(shipped,"mPlayerTexture",texture);window.surface=parent;
  window.reflow=()->{try{invoke(shipped,"cobraLayoutPlayerPanels");}catch(Exception e){throw new RuntimeException(e);}};CobraWindowReflow.install(window);
  for(int[] size:new int[][]{{480,1000},{1800,1500},{1500,1800},{360,220},{1800,1500},{480,1000}}){
   layout(parent,size[0],size[1]);parent.getViewTreeObserver().dispatchOnPreDraw();layout(parent,size[0],size[1]);assertEquals(size[0],texture.getWidth());assertEquals(size[1],texture.getHeight());
  }
  int before=window.calls;FrameLayout replacement=new FrameLayout(window);layout(replacement,480,1000);window.surface=replacement;
  parent.getViewTreeObserver().dispatchOnPreDraw();assertEquals(before+1,window.calls);
 }
}
