package com.projectinfinity.kodi;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.util.ReflectionHelpers;
import static org.junit.Assert.*;

/** Actual OS locks in separate processes, production reader, no Kodi native load. */
@RunWith(RobolectricTestRunner.class) @Config(sdk=35,manifest=Config.NONE)
public class KodiOwnerLeaseTest {
  File dir;final String owner=UUID.randomUUID().toString();final List<Process> children=new ArrayList<>();
  @Before public void before()throws Exception{dir=Files.createTempDirectory("kodi-owner-lease").toFile();}
  @After public void after()throws Exception{
    for(Process p:children){if(p.isAlive())p.destroyForcibly();p.waitFor(5,TimeUnit.SECONDS);}
    for(File f:dir.listFiles())f.delete();dir.delete();
  }
  JSONObject row(int schema,int pid,String token,String phase)throws Exception{
    JSONObject j=new JSONObject().put("schema",schema).put("pid",pid).put("owner",token).put("launch","selection")
      .put("began",1000).put("close_at",phase.equals("RUNNING")?0:2000).put("phase",phase).put("live",phase.equals("RUNNING")).put("error","");
    Files.write(new File(dir,InfinityKodiShutdown.STATE).toPath(),j.toString().getBytes(StandardCharsets.UTF_8));return j;
  }
  Process hold(String token)throws Exception{
    File path=InfinityKodiShutdown.leasePath(dir,token);Files.write(path.toPath(),new byte[0]);
    Process p=new ProcessBuilder("python3","-u","-c",
      "import fcntl,sys; f=open(sys.argv[1],'r+'); fcntl.lockf(f,fcntl.LOCK_EX); print('held',flush=True); sys.stdin.read()",
      path.getAbsolutePath()).redirectErrorStream(true).start();children.add(p);
    java.util.concurrent.ExecutorService wait=java.util.concurrent.Executors.newSingleThreadExecutor();
    try{assertEquals("held",wait.submit(()->new BufferedReader(new InputStreamReader(p.getInputStream())).readLine()).get(5,TimeUnit.SECONDS));}
    finally{wait.shutdownNow();}return p;
  }
  void stop(Process p)throws Exception{p.getOutputStream().close();assertTrue(p.waitFor(5,TimeUnit.SECONDS));assertEquals(0,p.exitValue());}
  InfinityKodiShutdown.Life life(){return (pid,token)->InfinityKodiShutdown.ownerAlive(dir,pid,token);}
  InfinityKodiShutdown.Snapshot read()throws Exception{return InfinityKodiShutdown.read(dir,life(),InfinityKodiShutdown.Snapshot.empty());}
  void receipt(int pid,long epoch)throws Exception{
    Files.write(new File(dir,"infinity-native-cleanup.json").toPath(),new JSONObject().put("pid",pid).put("epoch_ms",epoch)
      .put("milestone","native.CXBMCApp.Destroy.complete").toString().getBytes(StandardCharsets.UTF_8));
  }
  @Test public void legacyPidReusedByAnUnrelatedLiveProcessCannotBlockChooser()throws Exception{
    Process unrelated=hold(UUID.randomUUID().toString());row(1,(int)unrelated.pid(),"old-kodi","DESTROYING");
    assertTrue(unrelated.isAlive());assertFalse(read().alive);assertFalse(read().pending());assertFalse(read().complete);
  }
  @Test public void persistedLeaseFileAfterProcessExitOrRebootIsNotAlive()throws Exception{
    row(2,android.os.Process.myPid(),owner,"DESTROYING");Files.write(InfinityKodiShutdown.leasePath(dir,owner).toPath(),new byte[0]);
    assertFalse(read().pending());assertFalse(read().alive);assertFalse(read().complete);
  }
  @Test public void exactOwnerHeldBySeparateProcessRemainsPending()throws Exception{
    Process p=hold(owner);row(2,(int)p.pid(),owner,"DESTROYING");
    assertTrue(read().alive);assertTrue(read().pending());assertTrue(read().stalled());assertFalse(read().complete);
  }
  @Test public void processReleaseCannotLeaveAPersistedLeasePending()throws Exception{
    Process p=hold(owner);int pid=(int)p.pid();row(2,pid,owner,"DESTROYING");assertTrue(read().pending());stop(p);
    assertTrue(InfinityKodiShutdown.leasePath(dir,owner).exists());assertFalse(read().pending());assertFalse(read().complete);
  }
  @Test public void anotherOwnerLeaseCannotReviveAnOldRecord()throws Exception{
    Process p=hold(UUID.randomUUID().toString());row(2,(int)p.pid(),owner,"DESTROYING");
    assertTrue(p.isAlive());assertFalse(read().alive);assertFalse(read().pending());
  }
  @Test public void nativeReceiptCannotCompleteWhileLeaseIsHeld()throws Exception{
    Process p=hold(owner);row(2,(int)p.pid(),owner,"DESTROYING");receipt((int)p.pid(),3000);
    assertTrue(read().pending());assertFalse(read().complete);
  }
  @Test public void matchingNativeReceiptAndReleasedLeaseCompleteClose()throws Exception{
    Process p=hold(owner);int pid=(int)p.pid();row(2,pid,owner,"DESTROYING");receipt(pid,3000);stop(p);
    assertTrue(read().complete);assertFalse(read().pending());assertEquals(InfinityExitCompletion.Plan.Phase.COMPLETE,read().phase);
  }
  @Test public void oldReceiptsNeverCompleteANewInstance()throws Exception{
    row(2,123,owner,"DESTROYING");receipt(123,1999);assertFalse(read().complete);receipt(122,3000);assertFalse(read().complete);
  }
  @Test public void forcedExitIsNeverReportedAsSuccessfulCleanup()throws Exception{
    row(2,123,owner,"FORCED");receipt(123,3000);assertFalse(read().complete);assertEquals(InfinityExitCompletion.Plan.Phase.FORCED,read().phase);
  }
  @Test public void liveAcknowledgementRequiresTheExactHeldInstance()throws Exception{
    Process p=hold(owner);row(2,(int)p.pid(),owner,"RUNNING");assertTrue(read().live);assertFalse(read().pending());stop(p);assertFalse(read().live);
  }
  @Test public void missingStatusRevalidatesCachedOwnerRatherThanKeepingItForever()throws Exception{
    Process p=hold(owner);row(2,(int)p.pid(),owner,"DESTROYING");InfinityKodiShutdown.Snapshot cached=read();
    assertTrue(new File(dir,InfinityKodiShutdown.STATE).delete());assertTrue(InfinityKodiShutdown.read(dir,life(),cached).pending());
    stop(p);assertFalse(InfinityKodiShutdown.read(dir,life(),cached).pending());
  }
  @Test public void corruptStatusFallbackRevalidatesCachedOwner()throws Exception{
    Process p=hold(owner);row(2,(int)p.pid(),owner,"DESTROYING");InfinityKodiShutdown.Snapshot cached=read();
    Files.write(new File(dir,InfinityKodiShutdown.STATE).toPath(),"invalid".getBytes(StandardCharsets.UTF_8));
    try{read();fail();}catch(Exception expected){}
    assertTrue(InfinityKodiShutdown.recheck(life(),cached).pending());stop(p);assertFalse(InfinityKodiShutdown.recheck(life(),cached).pending());
  }
  @Test public void invalidOwnerCannotOpenPathsOutsideMonitorFiles()throws Exception{
    for(String token:new String[]{"../state","", "old-kodi", "/tmp/test"}){
      try{InfinityKodiShutdown.ownerAlive(dir,123,token);fail(token);}catch(IOException expected){}
    }
    assertFalse(InfinityKodiShutdown.ownerAlive(dir,0,owner));
  }
  @Test public void historicalCleanupReceiptCanBeConfirmedWithoutInventingALiveOwner()throws Exception{
    row(1,24758,"historical-owner","DESTROYING");receipt(24758,3000);
    assertTrue(read().complete);assertFalse(read().pending());assertFalse(read().alive);
  }
}
