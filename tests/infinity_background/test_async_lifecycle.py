#!/usr/bin/env python3
"""Execute the real old/new guide method and new lifecycle boundary with host doubles.

No sleeps for race ordering: latches force callback-after-destroy and enqueue/close.
Host verification is not a claim of Android device acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import infinity_cobra_async_lifecycle as fix


def method(text, name):
    # Existing Java has balanced braces in these methods, including strings/comments.
    match=re.search(r'  (?:private|protected|public) (?:static )?\w+ '+name+r'\([^)]*\)\s*\{',text)
    if not match: raise AssertionError('Missing method '+name)
    depth,end=1,match.end()
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[match.start():end]


HEADER=r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
class Looper {
 static final Thread MAIN=Thread.currentThread();
 static Thread myLooper(){return Thread.currentThread();}
 static Thread getMainLooper(){return MAIN;}
}
class Handler {
 final List<Runnable> queue=new ArrayList<>();
 synchronized boolean post(Runnable r){queue.add(r);return true;}
 synchronized void removeCallbacksAndMessages(Object token){queue.clear();}
 synchronized void removeCallbacks(Runnable r){queue.removeIf(x->x==r);}
 synchronized List<Runnable> take(){List<Runnable> q=new ArrayList<>(queue);queue.clear();return q;}
 synchronized int size(){return queue.size();}
 void drain(){for(Runnable r:take())r.run();}
}
class Parent {
 volatile boolean finishing,destroyed;
 boolean isFinishing(){return finishing;}
 boolean isDestroyed(){return destroyed;}
 protected void onDestroy(){destroyed=true;}
}
public class AsyncLifecycleTest extends Parent {
 static int checks;
 static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
 static void await(CountDownLatch latch){try{if(!latch.await(5,TimeUnit.SECONDS))throw new AssertionError("Latch timeout");}catch(InterruptedException e){throw new AssertionError(e);}}
 static void awaitIgnoringInterrupt(CountDownLatch latch){boolean interrupted=false;while(true){try{if(!latch.await(5,TimeUnit.SECONDS))throw new AssertionError("Latch timeout");break;}catch(InterruptedException e){interrupted=true;}}if(interrupted)Thread.currentThread().interrupt();}
 static void join(Thread thread){try{thread.join(5000);}catch(InterruptedException e){throw new AssertionError(e);}check(!thread.isAlive(),"thread completed");}
 static void terminated(ExecutorService io){try{check(io.awaitTermination(5,TimeUnit.SECONDS),"executor terminated");}catch(InterruptedException e){throw new AssertionError(e);}}
 final ExecutorService mIo;
 final Handler mMain=new Handler();
 final Runnable mAutoRefresh=()->{},mStallWatchdog=()->{},mProgressTicker=()->{},mHideMultiChrome=()->{};
 class Bridge{void close(){check(mCobraAsyncDestroyed,"terminal flag before device cleanup");}} Bridge mDeviceBridge=new Bridge();
 int released;
 void releaseSinglePlayer(){check(mCobraAsyncDestroyed,"terminal flag before single player release");released++;}
 void releaseMulti(){check(mCobraAsyncDestroyed,"terminal flag before multi player release");released++;}
 AsyncLifecycleTest(){this(Executors.newFixedThreadPool(3));}
 AsyncLifecycleTest(ExecutorService io){mIo=io;}
 static class LiveSource{String type="m3u",id="test-source",epgUrl="https://example.invalid/guide";}
 static class ProgramPair{}
 static class GuideProgram{}
 static class Prefs{String getString(String k,String d){return d;}}
 static class Features{boolean sourceEnabled(String id){return true;}}
 static class LiveException extends Exception{}
 final Prefs mPrefs=new Prefs();final Features mFeatures=new Features();
 final Map<String,ProgramPair> mGuide=new HashMap<>();
 final Map<String,ArrayList<GuideProgram>> mGuidePrograms=new HashMap<>();
 Object mPlayerOverlay,mMultiOverlay;
 final AtomicInteger requests=new AtomicInteger();int renders;
 String xtreamEpgUrl(LiveSource s){return s.epgUrl;}
 String httpGet(String url){requests.incrementAndGet();return "fixture";}
 Map<String,ProgramPair> parseXmlTv(String text){Map<String,ProgramPair> r=new HashMap<>();r.put("channel",new ProgramPair());return r;}
 Map<String,ArrayList<GuideProgram>> parseXmlTvPrograms(String text){return new HashMap<>();}
 void showLiveHome(){renders++;}
 void runOnUiThread(Runnable r){mMain.post(r);}
 static class CapturingExecutor extends AbstractExecutorService {
  volatile boolean stopped;Runnable captured;int reject;
  public void shutdown(){stopped=true;} public List<Runnable> shutdownNow(){stopped=true;return Collections.emptyList();}
  public boolean isShutdown(){return stopped;}public boolean isTerminated(){return stopped;}
  public boolean awaitTermination(long t,TimeUnit u){return stopped;}
  public void execute(Runnable r){if(reject==1){stopped=true;throw new RejectedExecutionException();}if(reject==2)throw new RejectedExecutionException();if(stopped)throw new RejectedExecutionException();captured=r;}
 }
'''
TESTS=r'''
 public static void main(String[] args)throws Exception{
  Looper.getMainLooper();
  // Reproduce the exact old method's fatal submission to a terminated executor.
  AsyncLifecycleTest legacy=new AsyncLifecycleTest();legacy.mIo.shutdownNow();terminated(legacy.mIo);
  boolean rejected=false;try{legacy.legacyLoadGuideAsync(new LiveSource());}catch(RejectedExecutionException expected){rejected=true;}
  check(rejected,"old RC2 guide method reproduces RejectedExecutionException");

  AsyncLifecycleTest healthy=new AsyncLifecycleTest();healthy.loadGuideAsync(new LiveSource());healthy.mIo.shutdown();terminated(healthy.mIo);healthy.mMain.drain();
  check(healthy.requests.get()==1&&healthy.renders==1&&healthy.mGuide.size()==1,"live guide request and UI update still work");healthy.onDestroy();

  AsyncLifecycleTest inline=new AsyncLifecycleTest();inline.publishCobraUi(()->inline.renders++);check(inline.renders==1&&inline.mMain.size()==0,"main-thread publication stays immediate");inline.onDestroy();
  inline.loadGuideAsync(new LiveSource());check(!inline.submitCobraIo(()->{throw new AssertionError();}),"late submit rejected without executing");inline.publishCobraUi(()->{throw new AssertionError();});check(inline.mMain.size()==0&&inline.requests.get()==0,"destroyed Activity accepts no callback or guide work");

  // Force an active network operation to ignore shutdown interruption and finish late.
  AsyncLifecycleTest late=new AsyncLifecycleTest();CountDownLatch started=new CountDownLatch(1),release=new CountDownLatch(1);AtomicReference<Throwable> error=new AtomicReference<>();
  late.submitCobraIo(()->{started.countDown();awaitIgnoringInterrupt(release);try{late.publishCobraUi(()->late.loadGuideAsync(new LiveSource()));}catch(Throwable t){error.set(t);}});
  await(started);late.onDestroy();release.countDown();terminated(late.mIo);late.mMain.drain();check(error.get()==null&&late.requests.get()==0&&late.renders==0,"source result after destroy cannot schedule guide or render");

  // A queued callback is both removable and guarded when already dequeued.
  AsyncLifecycleTest queued=new AsyncLifecycleTest();Thread producer=new Thread(()->queued.publishCobraUi(()->queued.loadGuideAsync(new LiveSource())));producer.start();join(producer);
  check(queued.mMain.size()==1,"worker publication queued");List<Runnable> alreadyDequeued=queued.mMain.take();queued.mMain.post(()->{throw new AssertionError("unremoved timer");});queued.onDestroy();
  check(queued.mMain.size()==0,"all owned delayed callbacks removed");for(Runnable r:alreadyDequeued)r.run();check(queued.requests.get()==0,"execution-time terminal check drops dequeued publication");

  CapturingExecutor capture=new CapturingExecutor();AsyncLifecycleTest dequeued=new AsyncLifecycleTest(capture);AtomicInteger count=new AtomicInteger();check(dequeued.submitCobraIo(count::incrementAndGet),"live task accepted");Runnable job=capture.captured;dequeued.onDestroy();job.run();check(count.get()==0,"already-dequeued IO task drops after destroy");
  CapturingExecutor race=new CapturingExecutor();race.reject=1;AsyncLifecycleTest raced=new AsyncLifecycleTest(race);check(!raced.submitCobraIo(count::incrementAndGet),"shutdown between check and execute is contained");raced.onDestroy();
  CapturingExecutor unexpected=new CapturingExecutor();unexpected.reject=2;AsyncLifecycleTest bad=new AsyncLifecycleTest(unexpected);boolean surfaced=false;try{bad.submitCobraIo(count::incrementAndGet);}catch(RejectedExecutionException expected){surfaced=true;}check(surfaced,"unrelated live-executor failure is not swallowed");bad.onDestroy();

  AsyncLifecycleTest finishing=new AsyncLifecycleTest();finishing.finishing=true;finishing.loadGuideAsync(new LiveSource());finishing.publishCobraUi(()->{throw new AssertionError();});check(!finishing.submitCobraIo(()->{throw new AssertionError();})&&finishing.requests.get()==0,"finishing check protects pre-onDestroy handoff gap");finishing.onDestroy();
  AsyncLifecycleTest frameworkDead=new AsyncLifecycleTest();frameworkDead.destroyed=true;check(!frameworkDead.submitCobraIo(()->{throw new AssertionError();}),"framework destroyed flag respected");frameworkDead.onDestroy();

  // Enqueue/teardown race: no late publication can survive clearing the private queue.
  for(int i=0;i<100;i++){
   AsyncLifecycleTest a=new AsyncLifecycleTest();CountDownLatch go=new CountDownLatch(1);Thread worker=new Thread(()->{await(go);for(int n=0;n<20;n++)a.publishCobraUi(()->a.loadGuideAsync(new LiveSource()));});worker.start();go.countDown();a.onDestroy();join(worker);a.mMain.drain();check(a.requests.get()==0&&a.mMain.size()==0,"concurrent publication cannot outlive teardown");
  }
  // An old instance never becomes live again; a separately created Activity works.
  AsyncLifecycleTest old=new AsyncLifecycleTest();old.onDestroy();old.onDestroy();AsyncLifecycleTest fresh=new AsyncLifecycleTest();old.publishCobraUi(()->{throw new AssertionError();});fresh.loadGuideAsync(new LiveSource());fresh.mIo.shutdown();terminated(fresh.mIo);fresh.mMain.drain();check(fresh.renders==1&&!old.isCobraAsyncAlive(),"recreation isolates stale and current instances");fresh.onDestroy();
  System.out.println("PASS: "+checks+" lifecycle race assertions; real RC2 failure reproduced, RC3 guide/callback boundary verified");
 }
}
'''


def run(before: Path,after: Path,out: Path):
    old,new=before.read_text(),after.read_text()
    assert hashlib.sha256(old.encode()).hexdigest()==fix.PREIMAGE
    assert new==fix.transform(old),'Candidate differs from reviewed transform'
    # Independent preservation checks: no background/playback/rotation policy rewrites.
    protected=('onConfigurationChanged','onResume','onPause','onStop','onUserLeaveHint',
      'onPictureInPictureModeChanged','onMultiWindowModeChanged','returnToInfinity',
      'configureCobraPip','enterCobraPictureInPicture','startCobraPlayer',
      'rememberAndPauseCobraPlayer','isCurrentCobraPlayer','pauseCobraForBackground',
      'resumeCobraAfterBackground','releaseSinglePlayer','releaseMulti','setMultiAudio')
    for name in protected:assert method(old,name)==method(new,name),name
    assert new.count('mIo.execute(')==1 and new.count('mIo.shutdownNow()')==1
    assert new.count('submitCobraIo(')==7 and new.count('publishCobraUi(')==11
    assert 'runOnUiThread(' not in new
    destroy=method(new,'onDestroy')
    assert destroy.index('closeCobraAsyncWork()')<destroy.index('releaseSinglePlayer()')
    assert 'mCobraAsyncDestroyed = false' in new and new.count('mCobraAsyncDestroyed = true')==1
    methods='\n'.join(method(new,n) for n in ('isCobraAsyncAlive','submitCobraIo','publishCobraUi','closeCobraAsyncWork','onDestroy','loadGuideAsync'))
    legacy=method(old,'loadGuideAsync').replace('loadGuideAsync(', 'legacyLoadGuideAsync(',1)
    harness=HEADER+fix.FIELDS+methods+'\n'+legacy+TESTS
    out.mkdir(parents=True,exist_ok=True)
    source=out/'AsyncLifecycleTest.java';source.write_text(harness)
    subprocess.run(['javac','-source','8','-target','8','-d',str(out),str(source)],check=True)
    result=subprocess.run(['java','-cp',str(out),'AsyncLifecycleTest'],check=True,capture_output=True,text=True,timeout=30)
    print(result.stdout,end='')
    report={'schema':1,'before_sha256':fix.PREIMAGE,'after_sha256':hashlib.sha256(new.encode()).hexdigest(),
      'protected_methods_byte_identical':list(protected),'guarded_io_sites':6,'guarded_ui_publications':10,
      'host_result':result.stdout.strip(),'device_tested':False}
    (out/'lifecycle-race-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 18 protected lifecycle/playback methods byte-identical; six IO and ten UI boundaries covered')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.before,a.after,a.out)
