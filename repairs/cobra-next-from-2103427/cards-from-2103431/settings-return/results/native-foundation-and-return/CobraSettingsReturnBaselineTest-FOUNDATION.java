package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.shadows.ShadowChoreographer;

/** Actual native shell/guide builders; instrumentation observes hierarchy only. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,application=Application.class,manifest=Config.NONE,
  qualifiers="w941dp-h1672dp-port-mdpi",instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraSettingsReturnBaselineTest {
  static Object get(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}
  static void set(Object o,String name,Object value)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);f.set(o,value);}
  static Object call(Object o,String name,Object...args)throws Exception{
    for(Method m:o.getClass().getDeclaredMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){m.setAccessible(true);try{return m.invoke(o,args);}catch(InvocationTargetException e){throw new RuntimeException("Actual method "+name+" failed",e.getCause());}}
    throw new NoSuchMethodException(name);
  }
  static Object construct(String name,Object...args)throws Exception{
    Class<?> c=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+name);
    for(Constructor<?> ctor:c.getDeclaredConstructors())if(ctor.getParameterCount()==args.length){ctor.setAccessible(true);return ctor.newInstance(args);}
    throw new NoSuchMethodException(name);
  }
  static void measure(View v,int w,int h){v.measure(View.MeasureSpec.makeMeasureSpec(w,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(h,View.MeasureSpec.EXACTLY));v.layout(0,0,w,h);}
  @Before public void pausedFrames(){ShadowChoreographer.setPaused(true);ShadowChoreographer.setFrameDelay(Duration.ofMillis(16));}
  static final class RecordIo extends AbstractExecutorService {
    final List<Runnable> admitted=new ArrayList<>();
    public void execute(Runnable r){admitted.add(r);}
    public void shutdown(){throw new AssertionError("No shutdown operation is selected");}
    public List<Runnable> shutdownNow(){throw new AssertionError("No shutdown operation is selected");}
    public boolean isShutdown(){return false;}public boolean isTerminated(){return false;}
    public boolean awaitTermination(long timeout,TimeUnit unit){throw new AssertionError("No shutdown operation is selected");}
  }
  static final class Fixture {
    final ActivityController<InfinityLiveActivity> controller;
    final InfinityLiveActivity a;final SharedPreferences prefs;final RecordIo io=new RecordIo();
    final List<Object> channels;final int width=941,height=1672;
    final List<String> hierarchy=new ArrayList<>();int addedGrids,removedGrids;
    Fixture()throws Exception{
      controller=Robolectric.buildActivity(InfinityLiveActivity.class);a=controller.get();a.setTheme(android.R.style.Theme_Material_NoActionBar);
      prefs=a.getSharedPreferences("settings-return-"+UUID.randomUUID(),Context.MODE_PRIVATE);
      prefs.edit().putString("cobra_appearance_mode","dark").putString("guide_view_mode","cards").putString("cobra_primary_view","guide").commit();
      set(a,"mPrefs",prefs);set(a,"mTheme",construct("Theme"));set(a,"mUi",construct("UiContract"));
      set(a,"mFeatures",new InfinityCobraFeatureRuntime(a));set(a,"mIo",io);
      set(a,"mCobraGuideStyle","cards");set(a,"mCobraGuideRoute","channels");set(a,"mCategory","ALL");set(a,"mSearch","");
      set(a,"mCobraProActive",false);set(a,"mCobraPreviewAutoplayAllowed",false);
      ((List<Object>)get(a,"mSources")).add(construct("LiveSource","qa","m3u","Synthetic QA","","","","https://example.invalid/playlist",""));
      channels=(List<Object>)get(a,"mChannels");
      for(int i=0;i<24;i++)channels.add(construct("Channel","qa:"+i,"Synthetic channel "+i,"Group","epg"+i,"","https://example.invalid/video/"+i,"qa",Collections.emptyMap()));
      set(a,"mGuidePreviewChannel",channels.get(0));
      call(a,"buildShell");call(a,"cobraShowGuideShell");controller.visible();
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(400));layout();
      assertNotNull(get(a,"mCobraGuideShell"));assertNotNull(get(a,"mCobraGuideList"));
      assertTrue(((View)get(a,"mCobraGuideShell")).isAttachedToWindow());
      assertTrue(get(a,"mCobraGuideList") instanceof GridView);
      assertEquals(24,((GridView)get(a,"mCobraGuideList")).getCount());
      assertNull(get(a,"mPlayer"));assertNull(get(a,"mCobraPreviewPlayer"));assertFalse((Boolean)get(a,"mCobraProActive"));
    }
    void layout(){measure(a.getWindow().getDecorView(),width,height);}
    void observeBrowser()throws Exception{
      ((ViewGroup)get(a,"mCobraGuideBrowser")).setOnHierarchyChangeListener(new ViewGroup.OnHierarchyChangeListener(){
        public void onChildViewAdded(View parent,View child){hierarchy.add("ADD "+child.getClass().getName());if(child instanceof GridView)addedGrids++;}
        public void onChildViewRemoved(View parent,View child){hierarchy.add("REMOVE "+child.getClass().getName());if(child instanceof GridView)removedGrids++;}
      });
    }
    JSONObject snapshot()throws Exception{
      GridView list=(GridView)get(a,"mCobraGuideList");JSONArray ids=new JSONArray();
      for(int i=0;i<list.getCount();i++)ids.put(get(list.getAdapter().getItem(i),"id"));
      JSONObject labels=new JSONObject();for(String field:new String[]{"mCobraGuideNowLabel","mCobraGuideNextLabel","mCobraModeDescription","mCobraModeSub"})labels.put(field,String.valueOf(((TextView)get(a,field)).getText()));
      JSONObject result=new JSONObject().put("mode",get(a,"mCobraGuideStyle")).put("route",get(a,"mCobraGuideRoute"))
        .put("category",get(a,"mCategory")).put("search",get(a,"mSearch")).put("list_key",get(a,"mCobraListStateKey"))
        .put("adapter_ids",ids).put("first_visible_position",list.getFirstVisiblePosition()).put("child_count",list.getChildCount())
        .put("labels",labels).put("submitted_IO_jobs",io.admitted.size()).put("added_GridViews",addedGrids).put("removed_GridViews",removedGrids)
        .put("hierarchy_events",new JSONArray(hierarchy)).put("selected_channel_id",get(get(a,"mGuidePreviewChannel"),"id"))
        .put("actual_shell_attached",((View)get(a,"mCobraGuideShell")).isAttachedToWindow())
        .put("window",new JSONArray(Arrays.asList(width,height))).put("source_requests",new JSONObject((Map)get(a,"mCobraEpgRequest")));
      return result;
    }
  }
  static void write(String name,JSONObject result)throws Exception{
    Path folder=Paths.get(System.getProperty("settings.output"));Files.createDirectories(folder);
    Files.write(folder.resolve(name+".json"),(result.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
    System.out.println("COBRA_SETTINGS_RETURN="+result.toString());
  }
  @Test public void actual431LoadedCardsSettingsReturn()throws Exception{
    Fixture f=new Fixture();f.observeBrowser();
    call(f.a,"cobraCaptureSettingsReturn");assertEquals(true,get(f.a,"mCobraSettingsReturnGuide"));
    call(f.a,"cobraReturnFromSettings");JSONObject synchronous=f.snapshot();
    f.layout();JSONObject measured=f.snapshot();
    assertEquals("cards",get(f.a,"mCobraGuideStyle"));assertFalse((Boolean)get(f.a,"mCobraSettingsReturnCaptured"));
    assertNull(get(f.a,"mPlayer"));assertNull(get(f.a,"mCobraPreviewPlayer"));
    assertEquals(24,((GridView)get(f.a,"mCobraGuideList")).getCount());
    write("LOADED_BASELINE",new JSONObject().put("phase","EXACT_SIGNED431_NATIVE_HOST_BASELINE")
      .put("status","OBSERVED_ACTUAL_SETTINGS_RETURN").put("synchronous",synchronous).put("after_native_measure",measured)
      .put("timing","NOT_MEASURED").put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN"));
  }
}
