package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;

/** Actual accepted431 projection or reviewed two-method prototype. No app lifecycle, UI, player or network. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35, application=Application.class, manifest=Config.NONE,
        instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraProjectionBenchmarkTest {
  static Object get(Object owner,String name)throws Exception {
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(owner);
  }
  static void set(Object owner,String name,Object value)throws Exception {
    Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);
  }
  static Object construct(String nested,Object...args)throws Exception {
    Class<?> c=Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+nested);
    for(Constructor<?> ctor:c.getDeclaredConstructors())if(ctor.getParameterCount()==args.length){
      ctor.setAccessible(true);return ctor.newInstance(args);
    }
    throw new NoSuchMethodException(nested);
  }
  static Method method(String name)throws Exception {
    Method m=InfinityLiveActivity.class.getDeclaredMethod(name);m.setAccessible(true);return m;
  }
  static final class Reads implements InvocationHandler {
    final SharedPreferences delegate;final SharedPreferences forwarding;
    final Map<String,Integer> counts=new LinkedHashMap<>();
    final Set<Object> hiddenDefaultIdentities=Collections.newSetFromMap(new IdentityHashMap<Object,Boolean>());
    Reads(SharedPreferences original){delegate=original;
      forwarding=(SharedPreferences)Proxy.newProxyInstance(SharedPreferences.class.getClassLoader(),
        new Class<?>[]{SharedPreferences.class},this);
    }
    public Object invoke(Object proxy,Method m,Object[] args)throws Throwable {
      if(m.getName().startsWith("get")&&args!=null&&args.length>0&&args[0] instanceof String){
        String key=m.getName()+":"+args[0];counts.put(key,counts.getOrDefault(key,0)+1);
        if(m.getName().equals("getStringSet")&&args[0].equals("cobra_hidden_channels"))
          hiddenDefaultIdentities.add(args[1]);
      }
      try{return m.invoke(delegate,args);}catch(InvocationTargetException e){throw e.getCause();}
    }
    void reset(){counts.clear();hiddenDefaultIdentities.clear();}
    int count(String key){return counts.getOrDefault(key,0);}
  }
  static final class Fixture {
    final InfinityLiveActivity a;final InfinityCobraFeatureRuntime features;
    final SharedPreferences prefs,featurePrefs;final Reads reads,featureReads;
    final List<Object> channels;final Set<String> favorites;final List<String> recents;
    final Method current=method("cobraChannelsForCurrentView"),guide=method("cobraGuideChannels");
    Fixture(int count,boolean adultExamples)throws Exception {
      // get() creates the object; onCreate/onStart/onResume are never called.
      a=Robolectric.buildActivity(InfinityLiveActivity.class).get();
      prefs=a.getSharedPreferences("projection-"+UUID.randomUUID(),Context.MODE_PRIVATE);
      set(a,"mPrefs",prefs);set(a,"mCobraGuideStyle","cards");set(a,"mCobraProActive",false);
      features=new InfinityCobraFeatureRuntime(a);set(a,"mFeatures",features);
      featurePrefs=(SharedPreferences)get(features,"prefs");
      List<Object> sources=(List<Object>)get(a,"mSources");
      for(String id:new String[]{"a","b"})sources.add(construct("LiveSource",id,"m3u","Synthetic "+id,"","","","https://example.invalid/"+id,""));
      channels=(List<Object>)get(a,"mChannels");favorites=(Set<String>)get(a,"mFavorites");recents=(List<String>)get(a,"mRecents");
      for(int i=0;i<count;i++){
        String name=adultExamples&&i==11?"XXX Channel":"Channel "+i;
        String group=adultExamples&&i==10?"Adult Specials":"Group"+(i%3);
        channels.add(channel(i,name,group));
      }
      reads=new Reads(prefs);featureReads=new Reads(featurePrefs);countReads(false);
    }
    Object channel(int i,String name,String group)throws Exception {
      String source=i%2==0?"a":"b";
      return construct("Channel",source+":"+i,name,group,"epg"+i,"","https://example.invalid/video/"+i,source,Collections.emptyMap());
    }
    void countReads(boolean enabled)throws Exception {
      set(a,"mPrefs",enabled?reads.forwarding:prefs);
      set(features,"prefs",enabled?featureReads.forwarding:featurePrefs);
      reads.reset();featureReads.reset();
    }
    List<Object> project(boolean sourceFiltered)throws Exception {
      return (List<Object>)(sourceFiltered?guide:current).invoke(a);
    }
    void state(String category,String query,String source)throws Exception {
      set(a,"mCategory",category);set(a,"mSearch",query);set(a,"mCobraGuideSource",source);
    }
    String id(int index)throws Exception{return (String)get(channels.get(index),"id");}
    String key(int index)throws Exception{return (index%2==0?"a":"b")+"|"+id(index);}
    void hidden(int...indices)throws Exception {
      Set<String> keys=new HashSet<>();for(int i:indices)keys.add(key(i));
      assertTrue(prefs.edit().putStringSet("cobra_hidden_channels",keys).commit());
    }
    void expect(boolean sourceFiltered,int...indices)throws Exception {
      List<Object> inventoryBefore=new ArrayList<>(channels);
      List<Object> actual=project(sourceFiltered);assertEquals(Arrays.toString(indices),indices.length,actual.size());
      assertEquals("Projection cannot change input inventory size",inventoryBefore.size(),channels.size());
      for(int i=0;i<inventoryBefore.size();i++)assertSame("Projection cannot reorder/replace input inventory",inventoryBefore.get(i),channels.get(i));
      for(int i=0;i<indices.length;i++)assertSame("Original channel identity/order at "+i,channels.get(indices[i]),actual.get(i));
    }
  }
  static void write(String name,JSONObject result)throws Exception {
    Path out=Paths.get(System.getProperty("projection.output"));Files.createDirectories(out);
    Files.write(out.resolve(name+".json"),(result.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
    System.out.println("COBRA_PROJECTION_"+name+"="+result.toString());
  }
  @Test public void actualSigned431ProjectionBaseline20226()throws Exception {
    Fixture f=new Fixture(20226,false);f.state("ALL","","");
    int expectedHidden=Integer.parseInt(System.getProperty("projection.expected.hidden.reads","20226"));
    int expectedDefaults=Integer.parseInt(System.getProperty("projection.expected.default.sets","20226"));
    String phase=System.getProperty("projection.phase","SIGNED431_BASELINE");
    JSONObject report=new JSONObject().put("scope","ACTUAL_PRODUCTION_DEX_HOST_PROJECTION").put("phase",phase)
      .put("inventory",20226).put("sources",2).put("warmups_per_entry",2).put("samples_per_entry",7)
      .put("timing_includes_read_counter_proxy",false).put("physical_Fold","NOT_RUN")
      .put("startup_or_frame_metric",false).put("shutdown","NOT_RUN");
    for(boolean sourceFiltered:new boolean[]{false,true}){
      String entry=sourceFiltered?"cobraGuideChannels":"cobraChannelsForCurrentView";
      f.countReads(false);for(int i=0;i<2;i++)assertEquals(20226,f.project(sourceFiltered).size());
      List<Double> times=new ArrayList<>();
      for(int i=0;i<7;i++){
        long start=System.nanoTime();List<Object> result=f.project(sourceFiltered);
        times.add((System.nanoTime()-start)/1000000.0);assertEquals(20226,result.size());
        for(int j=0;j<result.size();j++)assertSame(f.channels.get(j),result.get(j));
      }
      f.countReads(true);assertEquals(20226,f.project(sourceFiltered).size());
      int hidden=f.reads.count("getStringSet:cobra_hidden_channels");
      assertEquals("Selected phase must expose exact hidden preference read count",expectedHidden,hidden);
      assertEquals("Selected phase must expose exact distinct default set count",expectedDefaults,f.reads.hiddenDefaultIdentities.size());
      assertEquals("Existing profile JSON checks must remain untouched",40452,f.featureReads.count("getString:profiles"));
      assertEquals("Existing active-profile checks must remain untouched",40452,f.featureReads.count("getString:active_profile"));
      List<Double> sorted=new ArrayList<>(times);Collections.sort(sorted);
      JSONObject entryResult=new JSONObject().put("samples_ms",new JSONArray(times)).put("median_ms",sorted.get(3))
        .put("min_ms",sorted.get(0)).put("max_ms",sorted.get(6))
        .put("hidden_preference_reads_separate_count_call",hidden)
        .put("distinct_hidden_default_sets_separate_count_call",f.reads.hiddenDefaultIdentities.size())
        .put("feature_profiles_JSON_reads_separate_count_call",f.featureReads.count("getString:profiles"))
        .put("feature_active_profile_reads_separate_count_call",f.featureReads.count("getString:active_profile"));
      report.put(entry,entryResult);
    }
    write(phase.equals("SIGNED431_BASELINE")?"BASELINE":"PROTOTYPE",report);
  }
  @Test public void nextProjectionReflectsFiltersHiddenFavoritesRecentsInventoryAndProfile()throws Exception {
    Fixture f=new Fixture(12,true);f.state("ALL","","");f.expect(true,0,1,2,3,4,5,6,7,8,9,10,11);
    f.hidden(0);f.expect(true,1,2,3,4,5,6,7,8,9,10,11);
    f.state("ALL","","a");f.expect(true,2,4,6,8,10);
    f.state("Group1","","");f.expect(true,1,4,7);
    f.state("ALL"," Channel 2 ","");f.expect(true,2);
    f.state("ALL","gRoUp1","");f.expect(true,1,4,7);
    f.state("FAVORITES","","");f.favorites.add(f.id(1));f.favorites.add(f.id(4));f.expect(true,1,4);
    assertEquals("Temporary category reset must be restored","FAVORITES",get(f.a,"mCategory"));
    f.favorites.remove(f.id(1));f.favorites.add(f.id(3));f.expect(true,3,4);
    f.state("RECENT","does not match","");f.recents.addAll(Arrays.asList(f.id(11),f.id(2),"missing",f.id(1)));f.expect(true,11,2,1);
    f.hidden(0,2);f.expect(true,11,1);
    f.recents.clear();f.recents.addAll(Arrays.asList(f.id(11),f.id(11),f.id(1)));f.expect(true,11,11,1);
    assertTrue(f.prefs.edit().putString("cobra_custom_group|"+f.key(4),"Saved").putString("cobra_custom_group|"+f.key(7),"Saved").commit());
    f.state("MY:Saved","","");f.expect(true,4,7);
    assertTrue(f.prefs.edit().putString("cobra_custom_group|"+f.key(4),"Other").commit());f.expect(true,7);
    f.state("ALL","","");
    String locked=f.features.createProfile("Synthetic locked profile","",true);
    assertTrue(f.features.unlockAndSelectProfile(locked,""));
    f.expect(true,1,3,4,5,6,7,8,9);
    assertTrue(f.features.unlockAndSelectProfile("default",""));f.expect(true,1,3,4,5,6,7,8,9,10,11);
    Object old=f.channels.get(3),replacement=f.channel(3,"Replacement Channel","New Group");f.channels.set(3,replacement);
    f.state("New Group","","");f.expect(true,3);assertNotSame(old,f.project(true).get(0));
    f.state("ALL","","b");f.expect(true,1,3,5,7,9,11);
    write("SEMANTICS",new JSONObject().put("status","PASS_ACTUAL_SIGNED431_NEXT_CALL_FRESHNESS")
      .put("checks",new JSONArray(Arrays.asList("original_object_identity_order","source_filter","category","trimmed_casefolded_search",
        "hidden_set_changes","favorites_changes","recents_order_missing_and_duplicates","custom_group_changes",
        "profile_adult_lock_and_unlock","inventory_object_replacement")))
      .put("state","SYNTHETIC_HOST_PREFERENCES_ONLY").put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN"));
  }
}
