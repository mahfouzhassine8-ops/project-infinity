#!/usr/bin/env python3
"""Compile the actual runtime shutdown classes against Android and test their wire parser.

Unchanged UI/native peer APIs are narrow compile stubs; this is not a full APK build.
"""
import argparse
import pathlib
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=pathlib.Path, required=True)
parser.add_argument('--android-jar', type=pathlib.Path, required=True)
parser.add_argument('--native-receipt', type=pathlib.Path, help='SAFE JSON emitted by the actual native serializer harness')
args = parser.parse_args()
source = args.source / 'tools/android/packaging/xbmc/src'
names = ['InfinityCheckpointProtocol', 'InfinityCloseGuardService', 'InfinityCloseNativeLease',
         'InfinityExitCompletion', 'InfinityKodiShutdown', 'InfinityCloseProgress', 'InfinityHealthExport',
         'InfinityCheckpointAddonInstaller']
peers = '''package com.projectinfinity.kodi;
class Main extends android.app.Activity {
 static Main MainActivity;
 final InfinityExitCompletion.Plan mInfinityExitPlan=new InfinityExitCompletion.Plan();
 void infinityStopWeatherCapture(){}
 static Main infinityLiveActivity(){return MainActivity;}
 public native boolean infinityRequestPersistenceCheckpoint(String session,String owner,int pid);
 public native String infinityPersistenceCheckpointStatus(String session,String owner,int pid);
 public native boolean infinityAuthorizeCheckpointTermination(String session,String owner,int pid);
}
class Splash extends android.app.Activity {}
class InfinityExtendedBackgroundService extends android.app.Service {
 public android.os.IBinder onBind(android.content.Intent i){return null;}
}
class InfinityStartupTrace { static void mainEvent(String event){} }
class InfinityPowerMenuRoutes { static String report(android.content.Context c){return "";} }
class InfinityPowerControlActivity extends android.app.Activity {}
class R {static class drawable {static int notif_icon=1;}}
'''
test = '''package com.projectinfinity.kodi;
import org.json.*;
final class CheckpointWireTest {
 static final String S="00000000-0000-0000-0000-000000000001", O="00000000-0000-0000-0000-000000000002";
 static JSONObject valid()throws Exception {
  JSONObject row=new JSONObject();row.put("schema",1);row.put("session",S);row.put("owner",O);row.put("pid",42);
  row.put("generation",7);row.put("phase","SAFE_TO_TERMINATE");row.put("admission_sealed",true);
  row.put("required_owners",new JSONArray().put("settings"));
  row.put("owners",new JSONArray().put(new JSONObject().put("owner","settings").put("checkpoint_generation",7).put("generation",7)
   .put("durable_generation",7).put("dirty",false).put("dirty_before",true).put("dirty_remaining",false).put("result","COMMITTED").put("required_writes_finished",true)));
  return row;
 }
 static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
 static boolean accepted(JSONObject row){try{return InfinityCheckpointProtocol.safe(InfinityCheckpointProtocol.status(row.toString(),S,O,42));}catch(Exception invalid){return false;}}
 static void gates()throws Exception {
  String proof=InfinityCheckpointProtocol.proof("native-safe-receipt");
  InfinityCheckpointProtocol.AuthorizationGate gate=new InfinityCheckpointProtocol.AuthorizationGate(S,O,42,100,1100);
  check(!gate.consume(S,O,42,7,proof,101),"unarmed gate authorized");
  check(gate.arm(7,proof,101),"valid gate rejected");
  check(!gate.consume(O,O,42,7,proof,102),"wrong gate session authorized");
  check(!gate.consume(S,S,42,7,proof,102),"wrong gate owner authorized");
  check(!gate.consume(S,O,43,7,proof,102),"wrong gate PID authorized");
  check(!gate.consume(S,O,42,8,proof,102),"wrong gate generation authorized");
  check(!gate.consume(S,O,42,7,InfinityCheckpointProtocol.proof("other"),102),"wrong native proof authorized");
  check(gate.consume(S,O,42,7,proof,102),"matched gate rejected");
  check(!gate.consume(S,O,42,7,proof,103),"gate replay authorized");
  InfinityCheckpointProtocol.AuthorizationGate timeout=new InfinityCheckpointProtocol.AuthorizationGate(S,O,42,100,1100);
  check(timeout.arm(7,proof,101),"timeout gate not armed");check(!timeout.consume(S,O,42,7,proof,1100),"late permit authorized");
  for(int i=0;i<100;i++){
   final InfinityCheckpointProtocol.AuthorizationGate racing=new InfinityCheckpointProtocol.AuthorizationGate(S,O,42,100,1100);
   racing.arm(7,proof,101);final java.util.concurrent.CountDownLatch start=new java.util.concurrent.CountDownLatch(1);
   final java.util.concurrent.atomic.AtomicBoolean consumed=new java.util.concurrent.atomic.AtomicBoolean(),revoked=new java.util.concurrent.atomic.AtomicBoolean();
   Thread a=new Thread(()->{try{start.await();consumed.set(racing.consume(S,O,42,7,proof,102));}catch(InterruptedException e){throw new AssertionError(e);}});
   Thread b=new Thread(()->{try{start.await();revoked.set(racing.revoke());}catch(InterruptedException e){throw new AssertionError(e);}});
   a.start();b.start();start.countDown();a.join();b.join();check(!(consumed.get()&&revoked.get()),"revoked gate also consumed");
   check(!racing.consume(S,O,42,7,proof,103),"completed race left live gate");
  }
  System.out.println("PASS actual runtime authorization gate identity/deadline/replay and100 consume/revoke races");
 }
 static void completionReceipts()throws Exception {
  java.nio.file.Path directory=java.nio.file.Files.createTempDirectory("infinity-receipt-reader-");
  try{
   JSONObject state=new JSONObject().put("schema",2).put("pid",42).put("owner",O).put("launch","launch")
    .put("began",1).put("close_at",2).put("phase","CHECKPOINT_REQUESTED").put("live",false).put("error","");
   java.nio.file.Files.write(directory.resolve("infinity-kodi-process.json"),state.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
   String nativeJson=valid().toString();
   JSONObject receipt=new JSONObject().put("schema",1).put("pid",42).put("owner",O).put("session",S)
    .put("started_epoch_ms",10).put("started_elapsed_ms",100).put("phase","COMPLETE").put("checkpoint_saved",true)
    .put("generation",7).put("native_json",nativeJson).put("native_proof_sha256",InfinityCheckpointProtocol.proof(nativeJson));
   java.nio.file.Path path=directory.resolve(InfinityCheckpointProtocol.RECEIPT);
   java.nio.file.Files.write(path,receipt.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
   InfinityKodiShutdown.Snapshot result=InfinityKodiShutdown.read(directory.toFile(),(pid,owner)->false,InfinityKodiShutdown.Snapshot.empty());
   check(result.complete,"matched saved receipt+dead owner not complete");
   result=InfinityKodiShutdown.read(directory.toFile(),(pid,owner)->true,InfinityKodiShutdown.Snapshot.empty());
   check(!result.complete&&result.alive,"live owner falsely complete");
   receipt.put("phase","ENGINE_TERMINATING");java.nio.file.Files.write(path,receipt.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
   result=InfinityKodiShutdown.read(directory.toFile(),(pid,owner)->false,InfinityKodiShutdown.Snapshot.empty());
   check(!result.complete&&result.error.isEmpty(),"observer invented coordinator completion or false failure");
   receipt.put("phase","COMPLETE").put("native_proof_sha256",InfinityCheckpointProtocol.proof("wrong"));
   java.nio.file.Files.write(path,receipt.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
   result=InfinityKodiShutdown.read(directory.toFile(),(pid,owner)->false,InfinityKodiShutdown.Snapshot.empty());check(!result.complete,"bad proof completed");
   receipt.put("native_proof_sha256",InfinityCheckpointProtocol.proof(nativeJson)).put("owner",S);
   java.nio.file.Files.write(path,receipt.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
   JSONObject legacy=new JSONObject().put("pid",42).put("epoch_ms",99).put("milestone","native.CXBMCApp.Destroy.complete");
   java.nio.file.Files.write(directory.resolve("infinity-native-cleanup.json"),legacy.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
   result=InfinityKodiShutdown.read(directory.toFile(),(pid,owner)->false,InfinityKodiShutdown.Snapshot.empty());check(!result.complete,"stale owner or legacy cleanup certified checkpoint");
   System.out.println("PASS actual chooser receipt reader: identity, hash, live owner, authoritative completion and legacy isolation");
  }finally{
   try(java.util.stream.Stream<java.nio.file.Path> files=java.nio.file.Files.walk(directory)){
    files.sorted(java.util.Comparator.reverseOrder()).forEach(path->{try{java.nio.file.Files.delete(path);}catch(java.io.IOException e){throw new java.io.UncheckedIOException(e);}});
   }
  }
 }
 public static void main(String[] args)throws Exception {
  check(accepted(valid()),"valid proof rejected");
  JSONObject row=valid();row.put("session",O);check(!accepted(row),"wrong session accepted");
  row=valid();row.put("owner",S);check(!accepted(row),"wrong owner accepted");
  row=valid();row.put("pid",43);check(!accepted(row),"wrong PID accepted");
  row=valid();row.put("schema",2);check(!accepted(row),"wrong schema accepted");
  row=valid();row.put("admission_sealed",false);check(!accepted(row),"unsealed proof accepted");
  row=valid();row.put("owners",new JSONArray());check(!accepted(row),"empty owners accepted");
  row=valid();row.getJSONArray("required_owners").put("resume_hub");check(!accepted(row),"missing owner accepted");
  row=valid();row.getJSONArray("owners").put(row.getJSONArray("owners").getJSONObject(0));check(!accepted(row),"duplicate owner accepted");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("durable_generation",6);check(!accepted(row),"uncommitted generation accepted");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("checkpoint_generation",6);check(!accepted(row),"stale checkpoint generation accepted");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("required_writes_finished",false);check(!accepted(row),"unfinished writes accepted");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("result","FAILED");check(!accepted(row),"failed save accepted");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("dirty",true);check(!accepted(row),"current dirty state accepted");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("dirty_remaining",true);check(!accepted(row),"remaining dirty state accepted");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("dirty_before",false);check(!accepted(row),"unneeded commit treated as clean proof");
  row=valid();row.getJSONArray("owners").getJSONObject(0).put("dirty_before",false).put("result","ALREADY_DURABLE");check(accepted(row),"clean durable owner rejected");
  check(InfinityCheckpointProtocol.proof("abc").equals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),"SHA256 proof incorrect");
  System.out.println("PASS 18 actual Android wire/proof checks");
  gates();
  completionReceipts();
  if(args.length>0){
   String raw=new String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(args[0])),java.nio.charset.StandardCharsets.UTF_8);
   JSONObject fixture=new JSONObject(raw);
   check(InfinityCheckpointProtocol.safe(InfinityCheckpointProtocol.status(raw,fixture.getString("session"),fixture.getString("owner"),fixture.getInt("pid"))),"actual native-produced SAFE receipt rejected");
   System.out.println("PASS actual native EncodeStatus -> Android strict receipt parser");
  }
 }
}
'''
with tempfile.TemporaryDirectory(prefix='infinity-runtime-java-') as temp:
    work = pathlib.Path(temp)
    package = work / 'com/projectinfinity/kodi'
    package.mkdir(parents=True)
    for name in names:
        text = (source / (name + '.java.in')).read_text().replace('@APP_PACKAGE@', 'com.projectinfinity.kodi')
        (package / (name + '.java')).write_text(text)
    (package / 'PeerCompileStubs.java').write_text(peers)
    tv = package / 'channels/util/TvUtil.java'
    tv.parent.mkdir(parents=True)
    tv.write_text('package com.projectinfinity.kodi.channels.util; public class TvUtil { public static void cancelAllScheduledJobs(android.content.Context c){} }')
    (package / 'CheckpointWireTest.java').write_text(test)
    files = sorted(str(path) for path in work.rglob('*.java'))
    output = work / 'classes'
    subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '8', '-Xlint:deprecation',
                    '-classpath', str(args.android_jar), '-d', str(output)] + files, check=True)
    command = ['java', '-ea', '-cp', str(output) + ':' + str(args.android_jar),
               'com.projectinfinity.kodi.CheckpointWireTest']
    if args.native_receipt:
        command.append(str(args.native_receipt))
    subprocess.run(command, check=True)
exit_source = (source / 'InfinityExitCompletion.java.in').read_text()
assert 'Application.Quit' not in exit_source and 'request_string(QUIT)' not in exit_source
endpoint = (source / 'InfinityCloseNativeLease.java.in').read_text()
assert endpoint.count('android.os.Process.killProcess(') == 1
assert 'if(owner.infinityAuthorizeCheckpointTermination' in endpoint
assert 'consumeGuard(generation,proof)' in endpoint
assert 'BIND_AUTO_CREATE' not in (source / 'InfinityCloseGuardService.java.in').read_text()
print('PASS runtime route, explicit native authorization, and no-restart binding checks')
