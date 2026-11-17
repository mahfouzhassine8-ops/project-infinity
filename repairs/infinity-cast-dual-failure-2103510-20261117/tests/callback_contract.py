"""Execute exact source-extracted receiver-seek continuations with ordered SDK callbacks."""
from pathlib import Path
import subprocess,hashlib,json
ROOT=Path(__file__).resolve().parents[3];P='repairs/infinity-movies-continue-cast-2103486-20261112/cast/java/com/projectinfinity/kodi/InfinityCastSession.java';JAVA='/usr/lib/jvm/java-21-openjdk-amd64/bin/java';OUT=Path('/tmp/cast510-callback-contract');OUT.mkdir(exist_ok=True)
def program(source,original):
 start=source.index('            stage("receiver_seek"');end=source.index('\n        });\n    }\n    private boolean ownsMedia()',start);block=source[start:end]
 helper='' if original else next(line.strip() for line in source.splitlines() if line.strip().startswith('private boolean handoffActive('))
 common='''import java.util.function.Consumer;
public class SessionCallbackProbe {
 String token="token",mediaToken="media",message="",stageName="idle";boolean aborting,returning,cleanupPending,handedOff;long stageSerial;int failures;RemoteMediaClient remote=new RemoteMediaClient();
 static class InfinityCastDiagnostics{static void event(String a,String b,int c){}}
 static class MediaSeekOptions{static class Builder{Builder setPosition(long x){return this;}MediaSeekOptions build(){return new MediaSeekOptions();}}}
 static class Value{long optLong(String x){return 1000;}}
 static class Status{boolean ok;Status(boolean v){ok=v;}boolean isSuccess(){return ok;}int getStatusCode(){return ok?0:1;}}
 static class Result{Status status;Result(boolean v){status=new Status(v);}Status getStatus(){return status;}}
 static class Pending{Consumer<Result> callback;void setResultCallback(Consumer<Result> c){callback=c;}void complete(boolean ok){callback.accept(new Result(ok));}}
 static class RemoteMediaClient{Pending seek=new Pending(),play=new Pending();int plays;Pending seek(MediaSeekOptions options){return seek;}Pending play(){plays++;return play;}}
 void stage(String s,long t,String e){stageName=s;stageSerial++;}void fail(String a,String b,int code,String e){failures++;aborting=true;}void changed(){}void publish(){}
 HELP
 void register(){String expected=token,expectedMedia=mediaToken;Value value=new Value();final RemoteMediaClient receiver=remote;
 BLOCK
 }
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  SessionCallbackProbe ordinary=new SessionCallbackProbe();ordinary.register();ordinary.remote.seek.complete(true);check(ordinary.remote.plays==1&&ordinary.handedOff);ordinary.remote.play.complete(true);check(ordinary.failures==0);
  SessionCallbackProbe returned=new SessionCallbackProbe();returned.register();returned.returning=true;returned.stageSerial++;returned.remote.seek.complete(true);check(returned.remote.plays==EXPECTED_RETURN);
  if(EXPECTED_RETURN==0){
   int n=0;for(String kind:new String[]{"abort","cleanup","token","media","stage","remote"}){SessionCallbackProbe h=new SessionCallbackProbe();h.register();RemoteMediaClient pending=h.remote;
    switch(kind){case "abort":h.aborting=true;break;case "cleanup":h.cleanupPending=true;break;case "token":h.token="different";break;case "media":h.mediaToken="different";break;case "stage":h.stageSerial++;break;case "remote":h.remote=new RemoteMediaClient();break;}
    pending.seek.complete(true);check(pending.plays==0&&h.failures==0);n++;
   }
   SessionCallbackProbe rejected=new SessionCallbackProbe();rejected.register();rejected.remote.seek.complete(false);check(rejected.remote.plays==0&&rejected.failures==1);
   ordinary.remote.seek.complete(true);check(ordinary.remote.plays==1);System.out.println("PASS_ACTIVE_AND_STALE_SOURCE_CALLBACKS cases="+(n+4));
  }else System.out.println("REPRODUCED_BASELINE_PLAY_AFTER_RETURN");
 }
}'''.replace('HELP',helper).replace('BLOCK',block).replace('EXPECTED_RETURN','1' if original else '0')
 folder=OUT/('original' if original else 'corrected');folder.mkdir(exist_ok=True);p=folder/'SessionCallbackProbe.java';p.write_text(common)
 subprocess.run([JAVA,'--module','jdk.compiler/com.sun.tools.javac.Main','-d',str(folder),str(p)],check=True,capture_output=True,text=True)
 result=subprocess.run([JAVA,'-cp',str(folder),'SessionCallbackProbe'],check=True,capture_output=True,text=True)
 return dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),extracted_callback_sha256=hashlib.sha256(block.encode()).hexdigest(),result=result.stdout.strip())
old=subprocess.check_output(['git','show','cd682193dc78da29cfcfef83c5b0d43dec5b89a2:'+P],cwd=ROOT,text=True);new=(ROOT/P).read_text();r=dict(status='PASS_SOURCE_EXTRACTED_CALLBACK_ORDER',baseline=program(old,True),candidate=program(new,False),claim='Exact production seek/play continuations; controlled orderedSDKcallbacks. Not actualreceiver/phone acceptance.')
(ROOT/'repairs/infinity-cast-dual-failure-2103510-20261117/CALLBACK-HOST.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
