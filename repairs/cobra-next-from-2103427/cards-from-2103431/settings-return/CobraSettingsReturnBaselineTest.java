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
    final List<Object> channels;int width=941,height=1672;
    final List<String> hierarchy=new ArrayList<>();int addedGrids,removedGrids;
    Fixture()throws Exception{this(false,24);}
    Fixture(boolean seededEpg,int count)throws Exception{
      controller=Robolectric.buildActivity(InfinityLiveActivity.class);a=controller.get();a.setTheme(android.R.style.Theme_Material_NoActionBar);
      prefs=a.getSharedPreferences("settings-return-"+UUID.randomUUID(),Context.MODE_PRIVATE);
      prefs.edit().putString("cobra_appearance_mode","dark").putString("guide_view_mode","cards").putString("cobra_primary_view","guide").commit();
      set(a,"mPrefs",prefs);set(a,"mTheme",construct("Theme"));set(a,"mUi",construct("UiContract"));
      InfinityCobraFeatureRuntime features=new InfinityCobraFeatureRuntime(a);
      assertTrue(features.unlockAndSelectProfile("default",""));set(a,"mFeatures",features);set(a,"mIo",io);
      set(a,"mCobraGuideStyle","cards");set(a,"mCobraGuideRoute","channels");set(a,"mCategory","ALL");set(a,"mSearch","");
      set(a,"mCobraProActive",false);set(a,"mCobraPreviewAutoplayAllowed",false);
      ((List<Object>)get(a,"mSources")).add(construct("LiveSource","qa","m3u","Synthetic QA","","","","https://example.invalid/playlist",""));
      channels=(List<Object>)get(a,"mChannels");
      for(int i=0;i<count;i++)channels.add(construct("Channel","qa:"+i,i==23?"Adult synthetic channel":"Synthetic channel "+i,"Group","epg"+i,"","https://example.invalid/video/"+i,"qa",Collections.emptyMap()));
      if(seededEpg)seedEpg();
      set(a,"mGuidePreviewChannel",channels.get(0));
      call(a,"buildShell");call(a,"cobraShowGuideShell");controller.visible();
      Shadows.shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(400));layout();
      assertNotNull(get(a,"mCobraGuideShell"));assertNotNull(get(a,"mCobraGuideList"));
      assertTrue(((View)get(a,"mCobraGuideShell")).isAttachedToWindow());
      assertTrue(get(a,"mCobraGuideList") instanceof GridView);
      assertEquals(count,((GridView)get(a,"mCobraGuideList")).getCount());
      assertNull(get(a,"mPlayer"));assertNull(get(a,"mCobraPreviewPlayer"));assertFalse((Boolean)get(a,"mCobraProActive"));
    }
    void seedEpg()throws Exception{
      long now=org.robolectric.shadows.ShadowSystem.currentTimeMillis();
      Object data=construct("CobraEpgData");
      set(data,"identity",call(a,"cobraEpgIdentity",((List)get(a,"mSources")).get(0)));set(data,"fetched",now);
      Map<String,ArrayList<Object>> programs=(Map<String,ArrayList<Object>>)get(data,"programs");
      for(int i=0;i<channels.size();i++){
        ArrayList<Object> values=new ArrayList<>();
        for(int n=0;n<2;n++){Object p=construct("GuideProgram");set(p,"channel","epg"+i);set(p,"title",(n==0?"Current ":"Next ")+i);
          set(p,"description","Synthetic schedule description "+i);set(p,"start",now+(n==0?-3600000L:3600000L));set(p,"stop",now+(n==0?3600000L:7200000L));values.add(p);}
        programs.put("epg"+i,values);
      }
      ((Map<String,Object>)get(a,"mCobraEpg")).put("qa",data);
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
        .put("hierarchy_events",new JSONArray(hierarchy)).put("selected_channel_id",get(a,"mGuidePreviewChannel")==null?JSONObject.NULL:get(get(a,"mGuidePreviewChannel"),"id"))
        .put("actual_shell_attached",((View)get(a,"mCobraGuideShell")).isAttachedToWindow())
        .put("window",new JSONArray(Arrays.asList(width,height))).put("source_requests",new JSONObject((Map)get(a,"mCobraEpgRequest")))
        .put("native_shell_size",new JSONArray(Arrays.asList(((View)get(a,"mCobraGuideShell")).getWidth(),((View)get(a,"mCobraGuideShell")).getHeight())))
        .put("stored_scroll",new JSONObject((Map)get(a,"mCobraModeScroll")));
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
  @Test public void actual431BoundedCardsSettingsReturnSideEffects()throws Exception{
    JSONArray observations=new JSONArray();
    for(String scenario:new String[]{"loaded-nonzero-scroll","null-preview","uncached-EPG","changed-favorites-profile","theme-geometry"}){
      Fixture f=new Fixture(!scenario.equals("uncached-EPG"),scenario.equals("loaded-nonzero-scroll")?240:24);
      if(scenario.equals("loaded-nonzero-scroll")){
        GridView list=(GridView)get(f.a,"mCobraGuideList");list.setSelection(80);f.layout();
      }
      if(scenario.equals("changed-favorites-profile")){
        ((Set<String>)get(f.a,"mFavorites")).addAll(Arrays.asList("qa:0","qa:1","qa:23"));set(f.a,"mCategory","FAVORITES");
        call(f.a,"cobraRenderGuideBrowser");f.layout();
      }
      JSONObject before=f.snapshot();
      call(f.a,"cobraCaptureSettingsReturn");assertEquals(true,get(f.a,"mCobraSettingsReturnGuide"));
      if(scenario.equals("null-preview"))set(f.a,"mGuidePreviewChannel",null);
      if(scenario.equals("changed-favorites-profile")){
        Set<String> favorites=(Set<String>)get(f.a,"mFavorites");favorites.remove("qa:0");favorites.add("qa:4");
        InfinityCobraFeatureRuntime feature=(InfinityCobraFeatureRuntime)get(f.a,"mFeatures");
        String id=feature.createProfile("Synthetic return locked profile","",true);assertTrue(feature.unlockAndSelectProfile(id,""));
      }
      if(scenario.equals("theme-geometry")){
        f.prefs.edit().putString("cobra_appearance_mode","light").commit();f.width=760;f.height=1100;f.layout();
      }
      f.observeBrowser();int jobsBefore=f.io.admitted.size();
      call(f.a,"cobraReturnFromSettings");JSONObject synchronous=f.snapshot();f.layout();JSONObject after=f.snapshot();
      assertEquals("cards",get(f.a,"mCobraGuideStyle"));assertEquals(false,get(f.a,"mCobraProActive"));
      assertNull(get(f.a,"mPlayer"));assertNull(get(f.a,"mCobraPreviewPlayer"));
      assertEquals(false,get(f.a,"mCobraSettingsReturnCaptured"));
      GridView actual=(GridView)get(f.a,"mCobraGuideList");
      if(scenario.equals("changed-favorites-profile")){
        assertEquals(2,actual.getCount());assertSame(f.channels.get(1),actual.getAdapter().getItem(0));assertSame(f.channels.get(4),actual.getAdapter().getItem(1));
      }else assertEquals(f.channels.size(),actual.getCount());
      assertEquals("Only existing pending/fresh-source admission; return must not duplicate a guide job",jobsBefore,f.io.admitted.size());
      JSONObject observed=new JSONObject().put("scenario",scenario).put("before",before).put("synchronous_return",synchronous).put("after_native_measure",after);
      observations.put(observed);write("CASE-"+scenario,observed);
    }
    write("BOUNDED_SIDE_EFFECTS",new JSONObject().put("phase","EXACT_SIGNED431_NATIVE_HOST_BASELINE")
      .put("status","OBSERVED_FIVE_ACTUAL_SETTINGS_RETURN_CASES").put("cases",observations)
      .put("timing","NOT_MEASURED").put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN"));
  }

}
