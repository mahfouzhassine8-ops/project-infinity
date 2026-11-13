package com.projectinfinity.kodi;
import android.os.Handler;
public final class SessionCleanupTest {
 static int checks;static void check(boolean b,String m){checks++;if(!b)throw new AssertionError(m);}
 public static void main(String[] args)throws Exception {
  SessionContractTest.main(args);
  InfinityCastRelay.retireDelay=5000;InfinityCastChannel.retireDelay=6000;
  InfinityCastSession c=SessionContractTest.setup(1000,1000,1000);Handler.advance(5000);check(c.casting(),"real controller starts");c.returnToPhone();Handler.advance(5500);
  check(c.transferring(),"must retain cleanup ownership while actual relay/channel retirement is pending");check(!c.phone.paused,"phone already restored independently of draining relay");
  Handler.advance(12000);check(!c.transferring()&&c.phone.releases==1,"retirement callback completes cleanup exactly once");
  InfinityCastRelay.retireDelay=InfinityCastChannel.retireDelay=0;
  c=SessionContractTest.setup(1000,1000,1000);Handler.advance(5000);InfinityCastGateway.refuseRelease=true;c.returnToPhone();Handler.advance(6000);
  check(c.transferring(),"native release refusal must not claim session released");check(c.message.contains("not confirmed"),"release failure visible without private source details");InfinityCastGateway.refuseRelease=false;c.returnToPhone();Handler.advance(7000);check(!c.transferring()&&c.phone.releases==2,"explicit Disconnect retry releases retained token without another media load");
  InfinityCastDiagnostics.event("source","https://private.invalid?token=secret",1);
  for(int n=0;n<100;n++)InfinityCastDiagnostics.event("fixture","bounded",n);
  String summary=InfinityCastDiagnostics.summary();check(summary.split("\\n").length<=80 && summary.length()<9000,"RAM-only summary bounded");check(!summary.contains("fixture.invalid")&&!summary.contains("Bearer"),"failure summary excludes source and credentials");
  System.out.println("PASS_CAST_CLEANUP_COMPLETION checks="+checks+"; production controller; deterministic native/SDK backends, no receiver claim");
 }
}
