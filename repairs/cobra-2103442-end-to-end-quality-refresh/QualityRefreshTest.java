package com.projectinfinity.kodi;

import android.view.*;
import android.widget.*;
import java.lang.management.ManagementFactory;
import java.lang.reflect.*;
import java.text.SimpleDateFormat;
import java.util.*;
import org.json.*;
import org.junit.*;
import static org.junit.Assert.*;

/** Actual signed-owner native methods; synthetic EPG, controlled decoder.
 * Host elapsed/allocation measurements are not Android or physical Fold timings. */
public class QualityRefreshTest extends ProApprovedLayoutTest {
 static java.lang.reflect.Method method(Object owner,String name,Class<?>...types)throws Exception {
  Method m=owner.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m;
 }
 static JSONObject measure(Method m,Object owner,Object arg,int batch)throws Exception {
  com.sun.management.ThreadMXBean bean=(com.sun.management.ThreadMXBean)ManagementFactory.getThreadMXBean();
  bean.setThreadAllocatedMemoryEnabled(true);long tid=Thread.currentThread().getId();
  long[] times=new long[42],bytes=new long[42];Object result=null;
  for(int r=-21;r<42;r++){
   long b=bean.getThreadAllocatedBytes(tid),t=System.nanoTime();
   for(int i=0;i<batch;i++)result=m.invoke(owner,arg);
   t=System.nanoTime()-t;b=bean.getThreadAllocatedBytes(tid)-b;
   if(r>=0){times[r]=t;bytes[r]=b;}
  }
  Arrays.sort(times);Arrays.sort(bytes);
  return new JSONObject().put("batch",batch).put("warmups",21).put("samples",42)
   .put("p50_ms",times[21]/1e6).put("p95_ms",times[39]/1e6)
   .put("median_allocated_bytes",bytes[21]).put("result_nonnull",result!=null);
 }
 static Object program(String title,long start,long stop)throws Exception {
  Object p=CobraCardsLayoutTest.construct("GuideProgram");put(p,"channel","epg0");put(p,"title",title);put(p,"description","Synthetic EPG");put(p,"start",start);put(p,"stop",stop);return p;
 }
 @Test public void formattingAndGuideBaseline()throws Exception {
  CobraCardsLayoutTest.Fixture f=fixture("cards",1080,2520,480,"dark");
  Method format=method(f.a,"formatTime",long.class);long now=4102444800000L; // Fixed future fixture, independent of host/Android clock interception.
  assertEquals(new SimpleDateFormat("EEE MMM d • h:mm a",Locale.US).format(new Date(now)),format.invoke(f.a,now));
  JSONObject report=new JSONObject().put("environment","Host API35/Robolectric native graphics; synthetic data; no decoder")
   .put("format_500_labels",measure(format,f.a,now,500));
  Object data=((Map)get(f.a,"mCobraEpg")).get("qa");Map programs=(Map)get(data,"programs");
  ArrayList<Object> full=new ArrayList<>(),shortGuide=new ArrayList<>();
  for(int i=-24;i<144;i++)full.add(program("Full "+i,now+i*1800000L,now+(i+1)*1800000L));
  for(int i=-2;i<12;i++)shortGuide.add(program("Short "+i,now+i*1800000L,now+(i+1)*1800000L));
  programs.put("epg0",full);programs.put("@stream:qa:0",shortGuide);
  Method next=method(f.a,"cobraNextProgram",f.channels.get(0).getClass());
  assertEquals("Full -24",get(next.invoke(f.a,f.channels.get(0)),"title"));
  report.put("next_program_100_queries",measure(next,f.a,f.channels.get(0),100));
  save("QUALITY-PERFORMANCE",report);
 }
 @Test public void formattingFreshnessAndConcurrency()throws Exception {
  CobraCardsLayoutTest.Fixture f=fixture("mobile",1080,2520,480,"dark");Method format=method(f.a,"formatTime",long.class);
  long[] times={0L,-1L,1735732800000L,1741503599000L,1741503600000L,1762063200000L,1893456000000L};
  JSONArray cases=new JSONArray();
  for(String zone:new String[]{"UTC","America/New_York","Europe/Paris","Asia/Kathmandu","Pacific/Apia"}){
   TimeZone.setDefault(TimeZone.getTimeZone(zone));
   for(long time:times){String want=new SimpleDateFormat("EEE MMM d • h:mm a",Locale.US).format(new Date(time));assertEquals(want,format.invoke(f.a,time));}
   cases.put(zone);
  }
  // The accepted format deliberately remains US, irrespective of UI locale.
  Locale.setDefault(Locale.FRANCE);TimeZone.setDefault(TimeZone.getTimeZone("America/New_York"));
  List<Thread> threads=new ArrayList<>();List<Throwable> failures=Collections.synchronizedList(new ArrayList<>());
  for(int n=0;n<4;n++){Thread t=new Thread(()->{try{for(int i=0;i<150;i++){long time=times[i%times.length];assertEquals(new SimpleDateFormat("EEE MMM d • h:mm a",Locale.US).format(new Date(time)),format.invoke(f.a,time));}}catch(Throwable e){failures.add(e);}});threads.add(t);t.start();}
  for(Thread t:threads)t.join();assertTrue(failures.toString(),failures.isEmpty());
  save("QUALITY-FORMAT-FRESHNESS",new JSONObject().put("zones",cases).put("timestamps_per_zone",times.length).put("concurrent_callers",4).put("status","PASS_EXACT_ORIGINAL_LABELS"));
 }
 @Test public void modeScreenThemeMatrix()throws Exception {
  JSONArray cases=new JSONArray();
  CobraCardsLayoutTest.Fixture f=fixture("cards",1080,2520,480,"dark");interactivePlayer(f);
  Object player=f.player,channel=get(f.a,"mGuidePreviewChannel"),texture=get(f.a,"mCobraPreviewTexture");
  for(int[] pane:new int[][]{{1080,2520,480},{1600,1800,240},{1800,1600,240},{2520,1080,480},{720,1400,320}}){
   resize(f,pane);
   for(String theme:new String[]{"light","dark","oled"}){
    f.prefs.edit().putString("cobra_appearance_mode",theme).commit();call(f.a,"cobraRestyleGuide");frames();
    for(String mode:new String[]{"mobile","compact","grid","cards","focus"}){
     f.mode(mode);if(mode.equals("focus"))watching(f);
     View shell=(View)get(f.a,"mCobraGuideShell");AbsListView rows=list(f);
     assertTrue("Guide visible: "+mode,rows.isShown());assertTrue(rows.getWidth()>0&&rows.getHeight()>0);assertTrue(rows.getChildCount()>0);
     assertSame(player,get(f.a,"mCobraPreviewPlayer"));assertSame(channel,get(f.a,"mGuidePreviewChannel"));assertSame(texture,get(f.a,"mCobraPreviewTexture"));
     int oldCount=rows.getCount();call(f.a,"cobraRefreshProgrammeLabels");frames();assertEquals(oldCount,list(f).getCount());
     JSONObject one=new JSONObject().put("pane",new JSONArray(pane)).put("theme",theme).put("mode",mode)
      .put("shell",bounds(shell).toShortString()).put("list",bounds(list(f)).toShortString()).put("visible_rows",list(f).getChildCount()).put("same_player_texture_channel",true);
     if(mode.equals("cards"))one.put("columns",((GridView)list(f)).getNumColumns());
     if(mode.equals("focus")){one.put("expanded",list(f) instanceof GridView);if(list(f) instanceof GridView)paired(f);else originalGeometry(f);}
     cases.put(one);
    }
   }
  }
  save("QUALITY-MODE-SCREEN-THEME",new JSONObject().put("cases",cases).put("count",cases.length()).put("physical_Fold","NOT_TESTED"));
 }
 @Test public void guideProjectionFreshnessAndBounds()throws Exception {
  CobraCardsLayoutTest.Fixture f=fixture("cards",1080,2520,480,"dark");long future=4102444800000L;
  ArrayList<Object> full=new ArrayList<>(),shortGuide=new ArrayList<>();Random random=new Random(442);
  for(int i=0;i<80;i++)full.add(program("Full "+i,future+i*3600000L,future+(i+1)*3600000L));
  for(int i=0;i<18;i++)shortGuide.add(program("Short "+i,future+i*1800000L,future+(i+1)*1800000L));
  JSONArray outcomes=new JSONArray();
  for(int edit=0;edit<120;edit++){
   if(edit>0)switch(edit%6){
    case 0:put(full.get(random.nextInt(full.size())),"title","Updated "+edit);break;
    case 1:put(full.get(random.nextInt(full.size())),"start",future+random.nextInt(85)*3600000L);break;
    case 2:put(shortGuide.get(random.nextInt(shortGuide.size())),"stop",future+random.nextInt(85)*3600000L);break;
    case 3:Collections.swap(full,0,full.size()-1);break;
    case 4:shortGuide.set(0,program("Replacement "+edit,future-3600000L,future-1800000L));break;
    case 5:put(full.get(0),"description","Live metadata "+edit);break;
   }
   ArrayList expected=(ArrayList)call(f.a,"cobraMergeProgrammeRanges",full,shortGuide);
   ArrayList actual=CobraGuidePresentation.nextPrograms(f.a,full,shortGuide);
   assertEquals("Exact original merge length after edit "+edit,expected.size(),actual.size());
   for(int i=0;i<expected.size();i++)assertSame("Original identity/order after edit "+edit,expected.get(i),actual.get(i));
   assertSame("Unchanged query reuses validated projection",actual,CobraGuidePresentation.nextPrograms(f.a,full,shortGuide));
  }
  // Replacement lists, profile/source-like publication, large input bypass and hard bounds.
  for(int i=0;i<100;i++){
   ArrayList<Object> a=new ArrayList<>(),b=new ArrayList<>();for(int j=0;j<600;j++)a.add(program("Bound "+j,future+j*60000L,future+(j+1)*60000L));
   CobraGuidePresentation.nextPrograms(f.a,a,b);
  }
  Field states=CobraGuidePresentation.class.getDeclaredField("STATES");states.setAccessible(true);Object state=((Map)states.get(null)).get(f.a);
  assertTrue(((Map)get(state,"entries")).size()<=32);assertTrue((int)get(state,"retained")<=16384);
  ArrayList<Object> huge=new ArrayList<>();for(int i=0;i<4097;i++)huge.add(program("Uncached "+i,future+i*60000L,future+(i+1)*60000L));
  int retained=(int)get(state,"retained");ArrayList a=CobraGuidePresentation.nextPrograms(f.a,huge,new ArrayList());assertEquals(4097,a.size());assertEquals(retained,get(state,"retained"));
  save("QUALITY-GUIDE-FRESHNESS",new JSONObject().put("same_size_mutations_and_reorders",120).put("replacement_publications",100).put("retained_input_programs",get(state,"retained")).put("entries",((Map)get(state,"entries")).size()).put("large_schedule_bypass",true).put("status","PASS_EXACT_ORIGINAL_PRECEDENCE_AND_IDENTITY"));
 }
}
