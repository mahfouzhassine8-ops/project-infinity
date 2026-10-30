package com.projectinfinity.kodi;

import android.app.Application;
import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.robolectric.shadows.ShadowSystem;

/** Actual signed431 methods; counters never replace native setter behaviour. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35, application=Application.class, manifest=Config.NONE,
        instrumentedPackages={"com.projectinfinity.kodi"})
@LooperMode(LooperMode.Mode.PAUSED)
public class CobraProgrammePresentationBaselineTest {
  static Object get(Object o,String name)throws Exception {
    Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);
  }
  static void set(Object o,String name,Object value)throws Exception {
    Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);f.set(o,value);
  }
  static Class<?> nested(String name)throws Exception {
    return Class.forName("com.projectinfinity.kodi.InfinityLiveActivity$"+name);
  }
  static Object construct(String name,Class<?>[] types,Object...args)throws Exception {
    Constructor<?> c=nested(name).getDeclaredConstructor(types);c.setAccessible(true);return c.newInstance(args);
  }
  static Method entry(String name)throws Exception {
    Method m=InfinityLiveActivity.class.getDeclaredMethod(name);m.setAccessible(true);return m;
  }
  static String text(CharSequence s){return s==null?"":s.toString();}

  public static final class CountText extends TextView {
    int layouts; List<String> writes=new ArrayList<>();
    CountText(Context c){super(c);}
    @Override public void setText(CharSequence value,BufferType type){
      if(writes!=null)writes.add(text(value));
      super.setText(value,type);
    }
    @Override public void requestLayout(){layouts++;super.requestLayout();}
    void reset(){writes.clear();layouts=0;}
    JSONObject snapshot()throws Exception {
      return new JSONObject().put("setText_calls",writes.size()).put("written_values",new JSONArray(writes))
          .put("requestLayout_calls",layouts).put("text",text(getText()))
          .put("content_description",text(getContentDescription())).put("visibility",getVisibility());
    }
  }
  public static final class CountProgress extends ProgressBar {
    int layouts; List<Integer> writes=new ArrayList<>(),visibilityWrites=new ArrayList<>();
    CountProgress(Context c){super(c,null,android.R.attr.progressBarStyleHorizontal);setMax(1000);}
    @Override public synchronized void setProgress(int value){
      if(writes!=null)writes.add(value);super.setProgress(value);
    }
    @Override public void setVisibility(int value){
      if(visibilityWrites!=null)visibilityWrites.add(value);super.setVisibility(value);
    }
    @Override public void requestLayout(){layouts++;super.requestLayout();}
    void reset(){writes.clear();visibilityWrites.clear();layouts=0;}
    JSONObject snapshot()throws Exception {
      return new JSONObject().put("setProgress_calls",writes.size()).put("written_values",new JSONArray(writes))
          .put("setVisibility_calls",visibilityWrites.size()).put("visibility_values",new JSONArray(visibilityWrites))
          .put("requestLayout_calls",layouts).put("progress",getProgress()).put("max",getMax())
          .put("visibility",getVisibility()).put("content_description",text(getContentDescription()));
    }
  }
  static final class Fixture {
    final InfinityLiveActivity a=Robolectric.buildActivity(InfinityLiveActivity.class).get();
    final LinearLayout root=new LinearLayout(a),details=new LinearLayout(a),toolbar=new LinearLayout(a);
    final Map<String,CountText> labels=new LinkedHashMap<>();
    final CountProgress progress=new CountProgress(a);
    final Object mode,channel; final String style; final boolean activeDetails;
    final JSONObject programmePreconditions=new JSONObject();
    Fixture(String style,String scenario,boolean eyebrowGuard,boolean layoutGuard,long now)throws Exception {
      this.style=style;activeDetails=eyebrowGuard&&layoutGuard;
      set(a,"mPrefs",a.getSharedPreferences("presentation-"+UUID.randomUUID(),Context.MODE_PRIVATE));
      set(a,"mCobraGuideStyle",style);set(a,"mCobraProActive",false);
      root.setOrientation(LinearLayout.VERTICAL);details.setOrientation(LinearLayout.VERTICAL);
      for(String field:new String[]{"mCobraGuideNowLabel","mCobraGuideNextLabel","mCobraModeDescription",
          "mCobraModeEyebrow","mCobraModeSub","mCobraPlayerProgram","mCobraPlayerSchedule","mCobraPlayerUpcoming"}){
        CountText v=new CountText(a);v.setText("BEFORE "+field);labels.put(field,v);
        details.addView(v,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
        set(a,field,v);
      }
      details.addView(progress,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,16));
      root.addView(details,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));
      root.addView(toolbar,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,48));
      set(a,"mCobraGuideDetails",details);set(a,"mCobraModeToolbar",toolbar);set(a,"mCobraGuideProgress",progress);
      // The real mode-layout computes its details height and progress eligibility.
      Method solve=nested("CobraModeLayout").getDeclaredMethod("solve",String.class,int.class,int.class,float.class,boolean.class);
      solve.setAccessible(true);mode=solve.invoke(null,style,941,1672,1f,false);
      set(a,"mCobraModeLayout",layoutGuard?mode:null);
      if(!eyebrowGuard)set(a,"mCobraModeEyebrow",null);
      List<Object> sources=(List<Object>)get(a,"mSources");
      sources.add(construct("LiveSource",new Class<?>[]{String.class,String.class,String.class,String.class,
          String.class,String.class,String.class,String.class},"qa","m3u","Synthetic QA","","","","https://example.invalid/qa",""));
      channel=construct("Channel",new Class<?>[]{String.class,String.class,String.class,String.class,
          String.class,String.class,String.class,Map.class},"qa:1","Synthetic channel","QA","epg-one","",
          "https://example.invalid/video","qa",Collections.emptyMap());
      ((List<Object>)get(a,"mChannels")).add(channel);
      boolean absent=scenario.equals("absent"),unmatched=scenario.equals("unmatched");
      Object expectedCurrent=null,expectedNext=null;
      if(!absent){
        Object data=construct("CobraEpgData",new Class<?>[]{});
        Map<String,ArrayList<Object>> programs=(Map<String,ArrayList<Object>>)get(data,"programs");
        ArrayList<Object> schedule=new ArrayList<>();
        if(scenario.equals("expired"))schedule.add(program("Expired programme","Old description",now-172800000L,now-86400000L));
        else if(!unmatched){
          expectedCurrent=program("Current programme","Actual current description",now-43200000L,now+43200000L);
          schedule.add(expectedCurrent);
          if(!scenario.equals("current-only")){
            expectedNext=program("Next programme","Actual next description",now+43200000L,now+86400000L);
            schedule.add(expectedNext);
          }
        }
        if(!unmatched)programs.put("epg-one",schedule);
        ((Map<String,Object>)get(a,"mCobraEpg")).put("qa",data);
      }
      set(a,"mGuidePreviewChannel",scenario.equals("null-channel")?null:channel);
      set(a,"mPlaying",scenario.equals("null-channel")?null:channel);
      if(scenario.equals("null-channel")){expectedCurrent=null;expectedNext=null;}
      // Production is instrumented by Robolectric. Assert the real current/next
      // selection before accepting a case; test-host wallclock is not its clock.
      for(String name:new String[]{"cobraCurrentProgram","cobraNextProgram"}){
        Method query=InfinityLiveActivity.class.getDeclaredMethod(name,nested("Channel"));query.setAccessible(true);
        Object actual=query.invoke(a,get(a,"mGuidePreviewChannel"));
        assertSame("Actual programme identity precondition "+scenario+"/"+name,
            name.equals("cobraCurrentProgram")?expectedCurrent:expectedNext,actual);
        programmePreconditions.put(name,actual==null?JSONObject.NULL:get(actual,"title"));
      }
      // No lifecycle or screen builder: lay out only the native counter views.
      root.measure(View.MeasureSpec.makeMeasureSpec(941,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(1672,View.MeasureSpec.EXACTLY));
      root.layout(0,0,941,1672);
      for(CountText v:labels.values())v.reset();progress.reset();
    }
    Object program(String title,String description,long start,long stop)throws Exception {
      Object p=construct("GuideProgram",new Class<?>[]{});set(p,"channel","epg-one");set(p,"title",title);
      set(p,"description",description);set(p,"start",start);set(p,"stop",stop);return p;
    }
    JSONObject snapshot()throws Exception {
      JSONObject texts=new JSONObject();for(Map.Entry<String,CountText> e:labels.entrySet())texts.put(e.getKey(),e.getValue().snapshot());
      return new JSONObject().put("style",style).put("mode_details_guard_active",activeDetails).put("labels",texts)
          .put("guide_progress",progress.snapshot()).put("details_content_description",text(details.getContentDescription()))
          .put("computed_mode_details_box",new JSONArray(get(mode,"details")))
          .put("actual_programme_identity_preconditions",programmePreconditions)
          .put("lifecycle","NOT_CALLED").put("player_network","NOT_CONSTRUCTED");
    }
  }
  static JSONObject finalGuideState(JSONObject state)throws Exception {
    JSONObject result=new JSONObject(),labels=state.getJSONObject("labels");
    for(String field:new String[]{"mCobraGuideNowLabel","mCobraGuideNextLabel","mCobraModeDescription","mCobraModeEyebrow","mCobraModeSub"}){
      JSONObject v=labels.getJSONObject(field);result.put(field,new JSONObject().put("text",v.getString("text"))
          .put("content_description",v.getString("content_description")).put("visibility",v.getInt("visibility")));
    }
    JSONObject bar=state.getJSONObject("guide_progress");
    result.put("progress",new JSONObject().put("progress",bar.getInt("progress")).put("max",bar.getInt("max"))
        .put("visibility",bar.getInt("visibility")).put("content_description",bar.getString("content_description")));
    result.put("details_content_description",state.getString("details_content_description"));return result;
  }
  static void sameGuideState(JSONObject actual,JSONObject expected)throws Exception {
    for(String key:new String[]{"mCobraGuideNowLabel","mCobraGuideNextLabel","mCobraModeDescription","mCobraModeEyebrow","mCobraModeSub","progress"}){
      JSONObject x=actual.getJSONObject(key),y=expected.getJSONObject(key);
      for(Iterator<String> keys=x.keys();keys.hasNext();){String k=keys.next();assertEquals(key+"."+k,y.get(k),x.get(k));}
    }
    assertEquals(expected.getString("details_content_description"),actual.getString("details_content_description"));
  }
  static String sha(byte[] data)throws Exception {
    StringBuilder out=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(data))out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();
  }
  @Test public void actual431RefreshWritesAndFinalState()throws Exception {
    JSONArray cases=new JSONArray();
    assertTrue("Set only the disposable host framework clock",android.os.SystemClock.setCurrentTimeMillis(1793318400000L));
    long now=ShadowSystem.currentTimeMillis();
    List<String[]> selected=new ArrayList<>();
    for(String scenario:new String[]{"current-next","current-only","expired","absent","unmatched","null-channel"})selected.add(new String[]{"cards",scenario,"true","true"});
    selected.add(new String[]{"cards","current-next","false","true"});
    selected.add(new String[]{"cards","current-next","true","false"});
    for(String style:new String[]{"mobile","grid","compact","focus"})selected.add(new String[]{style,"current-next","true","true"});
    for(String[] c:selected){
      boolean eyebrow=Boolean.parseBoolean(c[2]),layout=Boolean.parseBoolean(c[3]);
      Fixture full=new Fixture(c[0],c[1],eyebrow,layout,now);entry("cobraRefreshProgrammeLabels").invoke(full.a);
      JSONObject actual=full.snapshot();
      JSONObject row=new JSONObject().put("style",c[0]).put("scenario",c[1]).put("full_refresh",actual);
      JSONObject labels=actual.getJSONObject("labels");
      // Hypothesis is checked against actual native setter calls, not a source-line count.
      assertEquals(full.activeDetails?2:1,labels.getJSONObject("mCobraGuideNowLabel").getInt("setText_calls"));
      assertEquals(full.activeDetails?2:1,labels.getJSONObject("mCobraGuideNextLabel").getInt("setText_calls"));
      if(full.activeDetails){
        Fixture direct=new Fixture(c[0],c[1],true,true,now);entry("cobraRefreshModeDetails").invoke(direct.a);
        JSONObject expected=direct.snapshot();sameGuideState(finalGuideState(actual),finalGuideState(expected));
        assertEquals(1,expected.getJSONObject("labels").getJSONObject("mCobraGuideNowLabel").getInt("setText_calls"));
        assertEquals(1,expected.getJSONObject("labels").getJSONObject("mCobraGuideNextLabel").getInt("setText_calls"));
        row.put("direct_mode_details",expected).put("final_guide_state_equal",true);
      }else row.put("direct_mode_details","NOT_SELECTED_GUARD_FALSE; ORIGINAL_PRELIMINARY_FALLBACK_RETAINED");
      JSONObject finalState=finalGuideState(actual);row.put("final_guide_state",finalState)
          .put("final_guide_state_sha256",sha(finalState.toString().getBytes(StandardCharsets.UTF_8)));
      cases.put(row);
    }
    JSONObject report=new JSONObject().put("scope","ACTUAL_SIGNED431_NATIVE_VIEW_PRESENTATION_BASELINE")
        .put("status","PASS_ACTUAL_NATIVE_WRITE_COUNTS_AND_FINAL_STATE")
        .put("cases",cases).put("case_count",cases.length()).put("clock_anchor_ms",now)
        .put("clock_domain","Controlled Robolectric Android/ShadowSystem wallclock; actual programme identity preconditions required")
        .put("timing_benchmark",false).put("render_or_frame_measurement",false)
        .put("physical_Fold","NOT_RUN").put("shutdown","NOT_RUN").put("production_changes","NONE");
    Path out=Paths.get(System.getProperty("presentation.output"));Files.createDirectories(out);
    Files.write(out.resolve("BASELINE.json"),(report.toString(2)+"\n").getBytes(StandardCharsets.UTF_8));
    System.out.println("COBRA_PRESENTATION_BASELINE="+report.toString());
  }
}
