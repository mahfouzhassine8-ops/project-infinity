/* SPDX-License-Identifier: GPL-2.0-or-later */
package com.projectinfinity.kodi;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.lang.reflect.*;
import org.json.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35)
public class LiveClosing329Test {
  static final String OWNER="22222222-2222-2222-2222-222222222222";
  static final long ORIGIN=2000000000L,NOW=90000000000L;
  private File dir;
  @Before public void setup()throws Exception{dir=Files.createTempDirectory("closing329").toFile();InfinityCloseProgress.display=null;}
  JSONObject event(int pid,long session,long seq,String kind,String phase,long span)throws Exception{
    return new JSONObject().put("schema",1).put("engine",InfinityCloseProgress.ENGINE).put("pid",pid)
      .put("session_start_ns",session).put("boot_ns",session+seq*1000000).put("seq",seq)
      .put("kind",kind).put("phase",phase).put("span_id",span);
  }
  String e(long seq,String kind,String phase,long span)throws Exception{return event(42,ORIGIN,seq,kind,phase,span).toString();}
  InfinityCloseProgress.Reader reader()throws Exception{
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);
    r.accept(e(0,"milestone","capture.begin",0),NOW);return r;
  }
  void write(String text)throws Exception{Files.write(new File(dir,InfinityCloseProgress.FILE).toPath(),text.getBytes(StandardCharsets.UTF_8));}
  @Test public void realBeginsAndEndsDriveStages()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(e(1,"begin","pre.save_settings",1),NOW);assertEquals("saving",r.current().name);
    r.accept(e(2,"end","pre.save_settings",1),NOW);r.accept(e(3,"begin","pre.stop_services",2),NOW);assertEquals("services",r.current().name);
    r.accept(e(4,"end","pre.stop_services",2),NOW);r.accept(e(5,"begin","scripts.join_remaining",3),NOW);assertEquals("scripts",r.current().name);
  }
  @Test public void noTimedStageAdvancement()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(e(1,"begin","scripts.join_remaining",1),NOW);
    for(int i=0;i<100;i++)assertEquals("scripts",r.current().name);
  }
  @Test public void outerCleanupDoesNotHideScriptJoin()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(e(1,"begin","application.cleanup",1),NOW);
    r.accept(e(2,"begin","scripts.join_remaining",2),NOW);assertEquals("scripts",r.current().name);
    r.accept(e(3,"end","scripts.join_remaining",2),NOW);assertEquals("cleanup",r.current().name);
  }
  @Test public void endIsNotCleanExit()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(e(1,"begin","application.cleanup",1),NOW);
    r.accept(e(2,"end","application.cleanup",1),NOW);assertFalse(r.exitRequested);assertEquals("waiting",r.current().name);
  }
  @Test public void exitRequestStillWaitsForActualOwnerDeath()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(e(1,"milestone","process.exit_requested",0),NOW);
    assertEquals("Waiting for Kodi to exit",r.current().text);
    r.accept(e(2,"begin","scripts.uninitialize",7),NOW);assertEquals("closing",r.current().name);
  }
  @Test public void ignoresWrongPidAndOldSamePidSession()throws Exception{
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);
    r.accept(event(41,ORIGIN,0,"milestone","capture.begin",0).toString(),NOW);assertEquals(-1,r.session);
    r.accept(event(42,500000000,0,"milestone","capture.begin",0).toString(),NOW);assertEquals(-1,r.session);
  }
  @Test public void rejectsForeignEngine()throws Exception{
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);
    r.accept(event(42,ORIGIN,0,"milestone","capture.begin",0).put("engine","unknown").toString(),NOW);assertEquals(-1,r.session);
  }
  @Test public void rejectsFarFuture()throws Exception{
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);
    r.accept(event(42,NOW+5000000000L,0,"milestone","capture.begin",0).toString(),NOW);assertEquals(-1,r.session);
  }
  @Test public void ignoresDifferentSessionAfterCapture()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(event(42,ORIGIN+1000000000,1,"begin","scripts.join_remaining",1).toString(),NOW);
    assertEquals("waiting",r.current().name);
  }
  @Test public void duplicateBeginCannotReopenEndedSpan()throws Exception{
    InfinityCloseProgress.Reader r=reader();String first=e(1,"begin","pre.stop_services",1);
    r.accept(first,NOW);r.accept(e(2,"end","pre.stop_services",1),NOW);r.accept(first,NOW);assertEquals("waiting",r.current().name);
  }
  @Test public void outOfOrderEndDoesNotLeaveFalseActiveSpan()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(e(2,"end","pre.stop_services",1),NOW);
    r.accept(e(1,"begin","pre.stop_services",1),NOW);assertEquals("waiting",r.current().name);
  }
  @Test public void partialLineWaitsUntilComplete()throws Exception{
    String row=e(1,"begin","scripts.join_remaining",1);int half=row.length()/2;
    write(e(0,"milestone","capture.begin",0)+"\n"+row.substring(0,half));
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);r.read(NOW);assertEquals("waiting",r.current().name);
    try(FileOutputStream out=new FileOutputStream(new File(dir,InfinityCloseProgress.FILE),true)){out.write((row.substring(half)+"\n").getBytes(StandardCharsets.UTF_8));}
    r.read(NOW);assertEquals("scripts",r.current().name);
  }
  @Test public void traceRotationRejectsPreviousRun()throws Exception{
    write(e(0,"milestone","capture.begin",0)+"\n"+e(1,"begin","pre.stop_services",1)+"\n");
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);r.read(NOW);assertEquals("services",r.current().name);
    write(event(41,ORIGIN,0,"milestone","capture.begin",0).toString()+"\n");r.read(NOW);assertEquals(-1,r.session);
  }
  @Test public void malformedAndBoundedDataRemainUnknown()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept("broken json",NOW);assertTrue(r.invalid);assertFalse(r.exitRequested);
    write(e(0,"milestone","capture.begin",0)+"\n"+new String(new char[9000]).replace('\0','x')+"\n");
    r.read(NOW);assertTrue(r.invalid);assertEquals(0,r.partial.size());
  }
  @Test public void eventLimitKeepsLastKnownStageNotSuccess()throws Exception{
    InfinityCloseProgress.Reader r=reader();r.accept(e(1,"begin","scripts.join_remaining",1),NOW);
    r.accept(e(2,"limit","capture.event_limit",0),NOW);assertTrue(r.limited);assertEquals("scripts",r.current().name);assertFalse(r.exitRequested);
  }
  @Test public void missingFileDoesNotBlockOrComplete()throws Exception{
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);r.read(NOW);assertEquals("waiting",r.current().name);assertFalse(r.exitRequested);
  }
  @Test public void onePollHasBoundedReads()throws Exception{
    StringBuilder text=new StringBuilder(e(0,"milestone","capture.begin",0)+"\n");
    for(int i=1;i<1000;i++)text.append(e(i,"milestone","jobs.waiting_active",0)).append('\n');write(text.toString());
    InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);r.read(NOW);assertTrue(r.offset<=InfinityCloseProgress.MAX_READ);
  }
  @Test public void popupRejectsStaleOrMalformedIdentity(){
    Application a=RuntimeEnvironment.getApplication();Intent i=InfinityClosingActivity.intent(a,42,OWNER,1000);
    assertTrue(InfinityClosingActivity.valid(i,1001));assertFalse(InfinityClosingActivity.valid(i,999));
    assertFalse(InfinityClosingActivity.valid(i,152000));assertFalse(InfinityClosingActivity.valid(i.putExtra(InfinityKodiShutdown.OWNER,"bad"),1001));
  }
  @Test public void popupHasIndependentPrivateProcess()throws Exception{
    Application a=RuntimeEnvironment.getApplication();ActivityInfo info=a.getPackageManager().getActivityInfo(new ComponentName(a,InfinityClosingActivity.class),0);
    assertFalse(info.exported);assertEquals(a.getPackageName(),info.processName);assertEquals(a.getPackageName()+".closing",info.taskAffinity);
  }
  @Test public void displayCannotAttachToDifferentOwner(){
    InfinityCloseProgress.Display s=new InfinityCloseProgress.Display(42,OWNER,1000,"scripts","Finishing scripts",false);
    assertTrue(s.matches(42,OWNER));assertFalse(s.matches(43,OWNER));assertFalse(s.matches(42,"another-owner"));
  }
  private String allText(View v){StringBuilder text=new StringBuilder();if(v instanceof TextView)text.append(((TextView)v).getText());
    if(v instanceof ViewGroup)for(int i=0;i<((ViewGroup)v).getChildCount();i++)text.append(' ').append(allText(((ViewGroup)v).getChildAt(i)));return text.toString();}
  @Test public void independentCardRepaintsFromGuardWithoutKodiRenderer()throws Exception{
    Application a=RuntimeEnvironment.getApplication();long at=SystemClock.elapsedRealtime();
    ActivityController<InfinityClosingActivity> c=Robolectric.buildActivity(InfinityClosingActivity.class,InfinityClosingActivity.intent(a,42,OWNER,at)).create().start().resume();
    try{InfinityCloseProgress.display=new InfinityCloseProgress.Display(42,OWNER,at,"scripts","Finishing scripts",false);
      shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(300));assertTrue(allText(c.get().getWindow().getDecorView()).contains("Finishing scripts"));
      InfinityCloseProgress.display=new InfinityCloseProgress.Display(42,OWNER,at,"cleanup","Cleaning up application resources",false);
      shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(300));assertTrue(allText(c.get().getWindow().getDecorView()).contains("Cleaning up application resources"));
    }finally{c.pause().stop().destroy();}
  }
  @Test public void replaySanitizedActualNativeEventShape()throws Exception{
    String text;try(InputStream in=getClass().getResourceAsStream("/closing-trace-fixtures.json")){assertNotNull(in);text=new String(in.readAllBytes(),StandardCharsets.UTF_8);}
    JSONArray runs=new JSONArray(text);
    for(int i=0;i<runs.length();i++){
      InfinityCloseProgress.Reader r=new InfinityCloseProgress.Reader(dir,42,1000);
      JSONArray rows=runs.getJSONArray(i);java.util.HashSet<String> observed=new java.util.HashSet<>();
      for(int j=0;j<rows.length();j++){
        JSONArray packed=rows.getJSONArray(j);
        JSONObject row=event(42,ORIGIN,packed.getLong(0),packed.getString(2),packed.getString(3),packed.getLong(4)).put("boot_ns",ORIGIN+packed.getLong(1));
        r.accept(row.toString(),NOW);observed.add(r.current().name);
      }
      assertTrue(observed.contains("services"));assertTrue(observed.contains("scripts"));assertEquals("closing",r.current().name);assertFalse(r.invalid);
    }
  }
  @Test public void nativeGuardDeadlineAndBindingUnchanged(){assertEquals(150000,InfinityCloseGuardService.MAX_PROTECTION_MS);assertEquals(Context.BIND_IMPORTANT,InfinityCloseGuardService.BIND_FLAGS);}
  @Test public void notificationCarriesRealStageAndIndeterminateProgress()throws Exception{
    InfinityCloseGuardService s=Robolectric.buildService(InfinityCloseGuardService.class).create().get();
    try{Field f=InfinityCloseGuardService.class.getDeclaredField("session");f.setAccessible(true);f.set(s,new InfinityCloseGuardService.Session(OWNER,OWNER,42,SystemClock.elapsedRealtime()));
      Method m=InfinityCloseGuardService.class.getDeclaredMethod("notice",String.class);m.setAccessible(true);
      Notification n=(Notification)m.invoke(s,"Finishing scripts");assertEquals("Finishing scripts",n.extras.getString(Notification.EXTRA_TEXT));
      assertTrue(n.extras.getBoolean(Notification.EXTRA_PROGRESS_INDETERMINATE));assertTrue(n.extras.getBoolean(Notification.EXTRA_SHOW_CHRONOMETER));
    }finally{s.onDestroy();}
  }
}
