package com.projectinfinity.kodi;
import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import java.io.*;
import java.lang.reflect.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowChoreographer;
import static org.junit.Assert.*;

/** Production Android views and real drawer actions; controlled data/no live decoding.
 * Critical: measure() NEVER calls cobraLayoutGuide/cobraRenderGuideBrowser. The old
 * test forced those calls and masked the same-size recreated-shell defect.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=34,application=Application.class,manifest=Config.NONE,qualifiers="w412dp-h915dp-port-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraNavigationUiTest {
  @Before public void clock(){ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));}
  static Object get(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
  static void put(Object o,String n,Object v)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
  static Object call(Object o,String n,Object... args)throws Exception{for(Method m:o.getClass().getDeclaredMethods())if(m.getName().equals(n)&&m.getParameterCount()==args.length){m.setAccessible(true);try{return m.invoke(o,args);}catch(InvocationTargetException e){throw new AssertionError(n,e.getCause());}}throw new NoSuchMethodException(n);}
  static Object construct(String n,Object... args)throws Exception{Class<?> c=Class.forName(InfinityLiveActivity.class.getName()+"$"+n);for(Constructor<?> ctor:c.getDeclaredConstructors())if(ctor.getParameterCount()==args.length){ctor.setAccessible(true);return ctor.newInstance(args);}throw new NoSuchMethodException(n);}
  void frames(int n){for(int i=0;i<n;i++)Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(16));}
  static class PendingIo extends AbstractExecutorService {
    final ArrayList<Runnable> tasks=new ArrayList<>();boolean shutdown;
    public void execute(Runnable r){if(shutdown)throw new RejectedExecutionException();tasks.add(r);}public void shutdown(){shutdown=true;}
    public List<Runnable> shutdownNow(){shutdown=true;ArrayList<Runnable> result=new ArrayList<>(tasks);tasks.clear();return result;}
    public boolean isShutdown(){return shutdown;}public boolean isTerminated(){return shutdown;}public boolean awaitTermination(long t,TimeUnit u){return shutdown;}
    void drain(){ArrayList<Runnable> copy=new ArrayList<>(tasks);tasks.clear();for(Runnable r:copy)r.run();}
  }
  @SuppressWarnings("unchecked") InfinityLiveActivity fixture(int channels)throws Exception {
    ActivityController<InfinityLiveActivity> controller=Robolectric.buildActivity(InfinityLiveActivity.class);
    InfinityLiveActivity a=controller.get();a.setTheme(android.R.style.Theme_Material_NoActionBar);
    SharedPreferences prefs=a.getSharedPreferences("cobra157fixture",Context.MODE_PRIVATE);prefs.edit().clear().putString("cobra_appearance_mode","dark").commit();
    put(a,"mPrefs",prefs);put(a,"mTheme",construct("Theme"));put(a,"mUi",construct("UiContract"));put(a,"mFeatures",new InfinityCobraFeatureRuntime(a));put(a,"mCobraPreviewAutoplayAllowed",false);
    ((ExecutorService)get(a,"mIo")).shutdownNow();put(a,"mIo",new PendingIo());
    List<Object> all=(List<Object>)get(a,"mChannels");Object data=construct("CobraEpgData");Map<String,Object> programs=(Map<String,Object>)get(data,"programs");
    String[] names={"Nature One","World News","Kids Planet","Cinema Plus","Sport Central","History Now","Discovery Lab","Travel Life"};
    long now=System.currentTimeMillis(),start=now-now%1800000L;
    for(int i=0;i<channels;i++){
      String id="fixture:"+i,key="ch"+i;Object c=construct("Channel",id,names[i%8]+(i<8?"":" "+i),i%2==0?"Documentaries":"Entertainment",key,"","","",Collections.emptyMap());all.add(c);
      if(i<64){ArrayList<Object> rows=new ArrayList<>();for(int j=0;j<8;j++){Object p=construct("GuideProgram");put(p,"channel",key);put(p,"start",start+(j-1)*1800000L);put(p,"stop",start+j*1800000L);put(p,"title",j%2==0?"Wild coastlines":"The evening report");put(p,"description","Generated guide data; no provider or video decoder is being simulated.");rows.add(p);}programs.put(key,rows);}
    }
    ((Map<String,Object>)get(a,"mCobraEpg")).put("",data);put(a,"mGuidePreviewChannel",all.get(0));((Set<String>)get(a,"mFavorites")).add("fixture:0");
    call(a,"buildShell");controller.visible();return a;
  }
  void measure(InfinityLiveActivity a,int w,int h)throws Exception{
    View decor=a.getWindow().getDecorView();
    for(int i=0;i<6;i++){
      decor.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));decor.layout(0,0,w,h);
      View shell=(View)get(a,"mCobraGuideShell"),video=(View)get(a,"mCobraGuideVideo");
      if(i==0&&shell!=null&&shell.isAttachedToWindow()){
        assertNotNull(video);
        assertTrue("Preview must have real bounds in the FIRST traversal, before advancing the clock",video.getWidth()>32&&video.getHeight()>24);
      }
      frames(1);
    }
  }
  void clean(InfinityLiveActivity a)throws Exception{((Handler)get(a,"mMain")).removeCallbacksAndMessages(null);((ExecutorService)get(a,"mIo")).shutdownNow();a.finish();}
  View description(View root,String exact){CharSequence c=root.getContentDescription();if(c!=null&&c.toString().equals(exact))return root;if(root instanceof ViewGroup)for(int i=0;i<((ViewGroup)root).getChildCount();i++){View found=description(((ViewGroup)root).getChildAt(i),exact);if(found!=null)return found;}return null;}
  void drawer(InfinityLiveActivity a,String destination)throws Exception{call(a,"toggleCobraDrawer");View drawer=a.getWindow().getDecorView().findViewWithTag("cobra_experience_drawer");assertNotNull(drawer);View row=description(drawer,destination);assertNotNull(destination,row);assertTrue(row.performClick());}
  int nodes(View v){int n=1;if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)n+=nodes(((ViewGroup)v).getChildAt(i));return n;}
  void guide(InfinityLiveActivity a)throws Exception{
    View shell=(View)get(a,"mCobraGuideShell"),video=(View)get(a,"mCobraGuideVideo"),texture=(View)get(a,"mCobraPreviewTexture");
    assertNotNull(shell);assertTrue("Guide must be attached",shell.isAttachedToWindow());assertTrue("Preview must not remain 1x1",video.getWidth()>32&&video.getHeight()>24);
    assertTrue("Texture must have actual visible bounds",texture.getWidth()>32&&texture.getHeight()>24);assertTrue(texture.isAttachedToWindow());
    assertEquals("Preview measured width must match assigned width",video.getLayoutParams().width,video.getMeasuredWidth());
    assertEquals("Preview measured height must match assigned height",video.getLayoutParams().height,video.getMeasuredHeight());
    assertEquals("Preview laid-out width must match its measurement",video.getMeasuredWidth(),video.getWidth());
    assertEquals("Preview laid-out height must match its measurement",video.getMeasuredHeight(),video.getHeight());
    assertEquals("Texture fills the preview width",video.getWidth(),texture.getWidth());
    assertEquals("Texture fills the preview height",video.getHeight(),texture.getHeight());
    AbsListView list=(AbsListView)get(a,"mCobraGuideList");assertNotNull("TV Grid must not be only groups",list);assertTrue(list.getHeight()>=48);assertTrue(list.getChildCount()>0);
    assertNotNull(shell.findViewWithTag("cobra_tv_time_ruler"));
    View browser=(View)get(a,"mCobraGuideBrowser");assertTrue("Guide reaches full usable right edge",Math.abs(browser.getRight()-shell.getWidth())<=2);
  }
  void image(InfinityLiveActivity a,String name)throws Exception{View view=(View)get(a,"mCobraGuideShell");File dir=new File(System.getProperty("cobra.evidence"));assertTrue(dir.isDirectory()||dir.mkdirs());Bitmap b=Bitmap.createBitmap(view.getWidth(),view.getHeight(),Bitmap.Config.ARGB_8888);view.draw(new Canvas(b));try(FileOutputStream out=new FileOutputStream(new File(dir,name+".png"))){assertTrue(b.compress(Bitmap.CompressFormat.PNG,100,out));}b.recycle();}

  @Test(timeout=90000) public void drawerReturnRemeasuresAtSameSizeAndDropsLateMovies()throws Exception{
    RuntimeEnvironment.setQualifiers("w412dp-h915dp-port-mdpi");InfinityLiveActivity a=fixture(192);
    try{
      drawer(a,"Live TV");measure(a,412,915);guide(a);
      for(String destination:new String[]{"Movies","Shows","Recordings","My List","Settings","Movies","Shows"}){
        View previous=(View)get(a,"mCobraGuideShell");drawer(a,destination);measure(a,412,915);
        drawer(a,"Live TV");measure(a,412,915);guide(a);assertNotSame("Disposed shell rebuilt on drawer return",previous,get(a,"mCobraGuideShell"));
        Object current=get(a,"mCobraGuideShell");((PendingIo)get(a,"mIo")).drain();frames(2);measure(a,412,915);
        assertSame("Delayed Movies/Shows must not replace live shell",current,get(a,"mCobraGuideShell"));guide(a);assertEquals("root",get(a,"mCobraInternalScreen"));
      }
      image(a,"tv-grid-after-drawer-return-412x915");
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void responsiveGuideAndContextualGroupsKeepTimeline()throws Exception{
    for(int[] size:new int[][]{{320,720},{412,915},{768,1024},{960,540}}){
      RuntimeEnvironment.setQualifiers("w"+size[0]+"dp-h"+size[1]+"dp-"+(size[0]>size[1]?"land":"port")+"-mdpi");InfinityLiveActivity a=fixture(192);
      try{
        call(a,"cobraOpenLiveTv");measure(a,size[0],size[1]);guide(a);Object texture=get(a,"mCobraPreviewTexture");
        call(a,"cobraOpenTvDirectory",false);measure(a,size[0],size[1]);guide(a);assertSame(texture,get(a,"mCobraPreviewTexture"));
        if(size[0]<760){assertNotNull(a.getWindow().getDecorView().findViewWithTag("cobra_tv_directory_overlay"));a.onBackPressed();assertNull(get(a,"mCobraActionSheet"));}
        else assertTrue(((View)get(a,"mCobraGuideDirectory")).getWidth()>0);
        call(a,"selectCobraCategory","Documentaries");measure(a,size[0],size[1]);guide(a);assertEquals(96,((AbsListView)get(a,"mCobraGuideList")).getCount());
        image(a,"tv-grid-"+size[0]+"x"+size[1]+"-dark");
        for(String mode:new String[]{"mobile","compact","cards","focus","grid"}){call(a,"cobraSwitchMode",mode);measure(a,size[0],size[1]);assertSame("Mode changes preserve TextureView",texture,get(a,"mCobraPreviewTexture"));assertNotNull(get(a,"mCobraGuideList"));}
      }finally{clean(a);}
    }
  }
  @Test(timeout=90000) public void systemDarkPreferencePersistsAndUsesSelectedPalette()throws Exception{
    RuntimeEnvironment.setQualifiers("w320dp-h720dp-port-mdpi");InfinityLiveActivity a=fixture(160);
    try{
      SharedPreferences prefs=(SharedPreferences)get(a,"mPrefs");call(a,"showSettings");call(a,"showCobraAppearancePicker");measure(a,320,720);View sheet=(View)get(a,"mCobraActionSheet");assertTrue(sheet.findViewWithTag("cobra-appearance:system").performClick());
      call(a,"showCobraAppearancePicker");measure(a,320,720);sheet=(View)get(a,"mCobraActionSheet");assertTrue(sheet.findViewWithTag("cobra-system-dark-picker").performClick());measure(a,320,720);sheet=(View)get(a,"mCobraActionSheet");assertTrue(sheet.findViewWithTag("cobra-system-dark:oled").performClick());
      assertEquals("system",prefs.getString("cobra_appearance_mode",""));assertEquals("oled",prefs.getString("cobra_system_dark_variant",""));
      for(boolean night:new boolean[]{true,false,true}){
        Configuration config=new Configuration(a.getResources().getConfiguration());config.uiMode=(config.uiMode&~Configuration.UI_MODE_NIGHT_MASK)|(night?Configuration.UI_MODE_NIGHT_YES:Configuration.UI_MODE_NIGHT_NO);config.fontScale=1.5f;a.getResources().updateConfiguration(config,a.getResources().getDisplayMetrics());
        a.onConfigurationChanged(config);assertEquals(night?"oled":"light",call(a,"cobraEffectiveAppearanceMode"));assertEquals("oled",prefs.getString("cobra_system_dark_variant",""));
        assertEquals("COBRA • SETTINGS",get(a,"mCobraStageTitle"));
      }
      call(a,"cobraOpenLiveTv");measure(a,320,720);guide(a);assertEquals("oled",prefs.getString("cobra_system_dark_variant",""));image(a,"tv-grid-320x720-system-oled-large-text");
      call(a,"buildShell");call(a,"cobraOpenLiveTv");measure(a,320,720);guide(a);assertEquals("oled",call(a,"cobraEffectiveAppearanceMode"));
    }finally{clean(a);}
  }
  @Test(timeout=90000) public void twelveThousandChannelGuideStaysVirtualized()throws Exception{
    RuntimeEnvironment.setQualifiers("w960dp-h540dp-land-mdpi");InfinityLiveActivity a=fixture(12000);
    try{call(a,"cobraOpenLiveTv");measure(a,960,540);guide(a);AbsListView list=(AbsListView)get(a,"mCobraGuideList");assertEquals(12000,list.getCount());assertTrue(list.getChildCount()<100);assertTrue(nodes((View)get(a,"mCobraGuideShell"))<1000);}finally{clean(a);}
  }
}
