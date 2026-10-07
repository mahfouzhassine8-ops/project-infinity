package com.projectinfinity.kodi;

import android.content.Intent;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class) @Config(sdk=35,manifest=Config.NONE)
public class KodiProcessStatusTest {
  File dir;
  @Before public void before()throws Exception{dir=Files.createTempDirectory("kodi-process-status").toFile();}
  @After public void after(){for(File f:dir.listFiles())f.delete();dir.delete();}
  void row(String phase,boolean live)throws Exception{
    JSONObject j=new JSONObject();j.put("schema",2);j.put("pid",123);j.put("owner","current-process");j.put("launch","selection");
    j.put("began",1000);j.put("close_at",phase.equals("RUNNING")?0:2000);j.put("phase",phase);j.put("live",live);j.put("error","");
    Files.write(new File(dir,InfinityKodiShutdown.STATE).toPath(),j.toString().getBytes(StandardCharsets.UTF_8));
  }
  void receipt(int pid,long epoch,String milestone)throws Exception{
    JSONObject j=new JSONObject();j.put("pid",pid);j.put("epoch_ms",epoch);j.put("milestone",milestone);
    Files.write(new File(dir,"infinity-native-cleanup.json").toPath(),j.toString().getBytes(StandardCharsets.UTF_8));
  }
  InfinityKodiShutdown.Snapshot read(boolean alive)throws Exception{return InfinityKodiShutdown.read(dir,(pid,owner)->alive,InfinityKodiShutdown.Snapshot.empty());}
  @Test public void activeKodiDoesNotCompleteFromTimeOrReceiptAlone()throws Exception{
    row("DESTROYING",false);receipt(123,3000,"native.CXBMCApp.Destroy.complete");
    InfinityKodiShutdown.Snapshot state=read(true);assertTrue(state.pending());assertFalse(state.complete);assertTrue(state.stalled());
    assertEquals(InfinityExitCompletion.Plan.Phase.DESTROYING,state.phase);
  }
  @Test public void nativeReceiptAndProcessDeathCompleteTheClose()throws Exception{
    row("DESTROYING",false);receipt(123,3000,"native.CXBMCApp.Destroy.complete");
    InfinityKodiShutdown.Snapshot state=read(false);assertFalse(state.pending());assertTrue(state.complete);assertFalse(state.alive);assertEquals("",state.error);
    assertEquals(InfinityExitCompletion.Plan.Phase.COMPLETE,state.phase);
  }
  @Test public void processDeathWithoutReceiptReportsFailureInsteadOfReady()throws Exception{
    row("DESTROYING",false);InfinityKodiShutdown.Snapshot state=read(false);assertFalse(state.complete);assertFalse(state.pending());assertFalse(state.error.isEmpty());
    assertEquals(InfinityExitCompletion.Plan.Phase.DESTROYING,state.phase);
  }
  @Test public void oldPidTimestampAndWrongMilestoneNeverConfirmCleanup()throws Exception{
    row("DESTROYING",false);
    for(Object[] bad:new Object[][]{{122,3000L,"native.CXBMCApp.Destroy.complete"},{123,1999L,"native.CXBMCApp.Destroy.complete"},{123,3000L,"exit.beforeNativeDestroy"}}){
      receipt((Integer)bad[0],(Long)bad[1],(String)bad[2]);assertFalse(read(false).complete);
    }
  }
  @Test public void javaOnDestroyReturnIsInsufficientForFullCircle()throws Exception{
    row("COMPLETE",false);assertFalse(read(true).complete);assertEquals(InfinityExitCompletion.Plan.Phase.DESTROYING,read(true).phase);
    assertFalse(read(false).complete);receipt(123,3000,"native.CXBMCApp.Destroy.complete");assertTrue(read(false).complete);
  }
  @Test public void forceCannotBecomeSuccessfulCleanup()throws Exception{
    row("FORCED",false);receipt(123,3000,"native.CXBMCApp.Destroy.complete");assertFalse(read(false).complete);
    assertEquals(InfinityExitCompletion.Plan.Phase.FORCED,read(false).phase);
  }
  @Test public void launchAcknowledgementRequiresLiveMatchingProcess()throws Exception{
    row("RUNNING",true);InfinityKodiShutdown.Snapshot live=read(true);assertTrue(live.live);assertEquals("selection",live.launch);assertFalse(live.pending());
    assertFalse(read(false).live);row("QUIT_QUEUED",true);assertTrue(read(true).pending());
  }
  @Test public void staleForceOwnerCannotTargetANewProcess(){
    Intent stale=new Intent().putExtra(InfinityKodiShutdown.PID,android.os.Process.myPid()).putExtra(InfinityKodiShutdown.OWNER,"old-owner");assertFalse(InfinityKodiShutdown.expected(stale));
    String owner=ReflectionHelpers.getStaticField(InfinityKodiShutdown.class,"processToken");stale.putExtra(InfinityKodiShutdown.OWNER,owner);assertTrue(InfinityKodiShutdown.expected(stale));
    stale.putExtra(InfinityKodiShutdown.PID,-1);assertFalse(InfinityKodiShutdown.expected(stale));
  }
}
