#!/usr/bin/env python3
"""Reproduce the RC2 shutdown rejection and test real RC3 method bodies on a host JVM.

Android Handler/Activity are deterministic test doubles; the executor is real.
A device test remains necessary. No network, credentials or sleep-based races.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from infinity_async_lifecycle_repair import LIVE, GRADLE, RC2_SHA, transform, digest
spec = importlib.util.spec_from_file_location('background_test', Path(__file__).with_name('test_background.py'))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
method = mod.method

PREFIX = r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
class Looper {
 static final Looper MAIN=new Looper();
 static final ThreadLocal<Boolean> UI=ThreadLocal.withInitial(()->false);
 static Looper myLooper(){return UI.get()?MAIN:null;}
}
class Handler {
 final List<Runnable> queue=Collections.synchronizedList(new ArrayList<>());
 Looper getLooper(){return Looper.MAIN;}
 boolean post(Runnable r){queue.add(r);return true;}
 boolean postDelayed(Runnable r,long ms){return post(r);}
 void removeCallbacks(Runnable r){synchronized(queue){queue.removeIf(x->x==r);}}
 void removeCallbacksAndMessages(Object token){queue.clear();}
 Runnable take(){synchronized(queue){return queue.isEmpty()?null:queue.remove(0);}}
 void drain(){Looper.UI.set(true);try{Runnable r;while((r=take())!=null)r.run();}finally{Looper.UI.set(false);}}
}
class Parent {protected void onDestroy(){}}
class LiveSource {String id="fixture",type="m3u",epgUrl="test://guide";}
class ProgramPair {}
class GuideProgram {}
class Prefs {String getString(String k,String d){return d;}}
class Features {boolean sourceEnabled(String id){return true;}}
'''
FIELDS = r'''
 ExecutorService mIo;
 final Handler mMain=new Handler();
 volatile boolean finishing,destroyed;
 boolean isFinishing(){return finishing;}
 boolean isDestroyed(){return destroyed;}
 Object mPlayerOverlay,mMultiOverlay;
 final Prefs mPrefs=new Prefs();final Features mFeatures=new Features();
 final Map<String,ProgramPair> mGuide=new HashMap<>();
 final Map<String,ArrayList<GuideProgram>> mGuidePrograms=new HashMap<>();
 AtomicInteger downloads=new AtomicInteger(),ui=new AtomicInteger();
 String xtreamEpgUrl(LiveSource s){return s.epgUrl;}
 String httpGet(String url){downloads.incrementAndGet();return "fixture";}
 Map<String,ProgramPair> parseXmlTv(String x){Map<String,ProgramPair> m=new HashMap<>();m.put("fixture",new ProgramPair());return m;}
 Map<String,ArrayList<GuideProgram>> parseXmlTvPrograms(String x){return new HashMap<>();}
 void showLiveHome(){ui.incrementAndGet();}
 void runOnUiThread(Runnable r){mMain.post(r);}
'''
TESTS = r'''
 static int checks;
 static void check(boolean b,String text){checks++;if(!b)throw new AssertionError(text);}
 static void await(CountDownLatch x)throws Exception{check(x.await(5,TimeUnit.SECONDS),"bounded await");}
 static void idle(ExecutorService e)throws Exception{e.submit(()->{}).get(5,TimeUnit.SECONDS);}
 static class ShutdownRace extends AbstractExecutorService {
  boolean down;
  public boolean isShutdown(){return down;}public boolean isTerminated(){return down;}
  public void shutdown(){down=true;}public List<Runnable> shutdownNow(){down=true;return Collections.emptyList();}
  public boolean awaitTermination(long n,TimeUnit u){return down;}
  public void execute(Runnable r){down=true;throw new RejectedExecutionException("deterministic check/execute race");}
 }
 public static void main(String[] args)throws Exception{
  GateTest a=new GateTest(Executors.newSingleThreadExecutor());
  a.loadGuideAsync(new LiveSource());idle(a.mIo);a.mMain.drain();
  check(a.downloads.get()==1&&a.ui.get()==1&&a.mGuide.size()==1,"healthy guide still downloads/publishes");a.stopCobraAsync();
  a=new GateTest(Executors.newSingleThreadExecutor());a.finishing=true;
  a.loadGuideAsync(new LiveSource());check(!a.submitCobraIo(()->{throw new AssertionError();}),"finishing rejects work");
  check(!a.postCobraUi(()->{throw new AssertionError();}),"finishing rejects UI");a.stopCobraAsync();
  a=new GateTest(Executors.newSingleThreadExecutor());a.destroyed=true;
  check(!a.postCobraDelayed(()->{},1)&&!a.submitCobraIo(()->{}),"Android destroyed flag also guards");a.stopCobraAsync();
  a=new GateTest(Executors.newSingleThreadExecutor());GateTest old=a;
  // Exactly the crash shape: source completion schedules guide work after teardown.
  a.postCobraUi(()->old.loadGuideAsync(new LiveSource()));Runnable alreadyDequeued=a.mMain.take();
  a.onDestroy();alreadyDequeued.run();
  check(a.downloads.get()==0&&a.mMain.queue.isEmpty(),"late completion cannot submit EPG or touch UI");
  check(a.releaseSawDead==2,"fence precedes both player release operations");
  check(!a.postCobraUi(()->{throw new AssertionError();}),"late worker callback refused");
  Looper.UI.set(true);check(!a.postCobraUi(()->{throw new AssertionError();}),"late immediate UI callback refused");Looper.UI.set(false);
  a=new GateTest(new ShutdownRace());AtomicInteger callerWork=new AtomicInteger();
  check(!a.submitCobraIo(callerWork::incrementAndGet)&&callerWork.get()==0,"check/execute rejection contained; never CallerRuns");a.stopCobraAsync();
  a=new GateTest(Executors.newSingleThreadExecutor());GateTest busy=a;
  CountDownLatch started=new CountDownLatch(1),release=new CountDownLatch(1),done=new CountDownLatch(1);
  a.submitCobraIo(()->{started.countDown();boolean interrupted=false;for(;;){try{release.await();break;}catch(InterruptedException e){interrupted=true;}}
    busy.postCobraUi(busy.ui::incrementAndGet);if(interrupted)Thread.currentThread().interrupt();done.countDown();});
  await(started);a.stopCobraAsync();check(done.getCount()==1,"teardown does not await a blocked worker");release.countDown();await(done);a.mMain.drain();
  check(a.ui.get()==0,"in-flight result discarded after destruction");
  a=new GateTest(Executors.newSingleThreadExecutor());Runnable timer=()->{};
  check(a.postCobraDelayed(timer,250),"live timers accepted");a.mMain.removeCallbacks(timer);
  check(a.mMain.queue.isEmpty(),"original cancellation identity retained");
  Handler unrelated=new Handler();unrelated.post(()->{});
  a.postCobraDelayed(()->{},650);a.postCobraDelayed(()->{},5500);a.postCobraUi(()->{});a.stopCobraAsync();a.stopCobraAsync();
  check(a.mMain.queue.isEmpty()&&unrelated.queue.size()==1,"all owned callbacks cleared; unrelated handler untouched");
  check(!a.postCobraDelayed(timer,1)&&!a.submitCobraIo(()->{}),"closed Activity never reopens its executor");
  GateTest fresh=new GateTest(Executors.newSingleThreadExecutor());Looper.UI.set(true);
  check(fresh.postCobraUi(fresh.ui::incrementAndGet)&&fresh.ui.get()==1,"new Activity works; UI thread stays immediate");Looper.UI.set(false);fresh.stopCobraAsync();
  // Worker enqueue versus UI-thread destruction, exercising the enqueue/clear lock.
  for(int i=0;i<100;i++){
   GateTest race=new GateTest(Executors.newSingleThreadExecutor());CountDownLatch go=new CountDownLatch(1);
   Thread worker=new Thread(()->{try{go.await();race.postCobraUi(race.ui::incrementAndGet);}catch(InterruptedException e){throw new AssertionError(e);}});
   worker.start();go.countDown();race.stopCobraAsync();worker.join(5000);
   check(!worker.isAlive()&&race.mMain.queue.isEmpty()&&race.ui.get()==0,"post/destroy race "+i);
  }
  System.out.println("PASS: "+checks+" RC3 lifecycle assertions, including 100 enqueue/destroy races");
 }
}'''


def compile_run(out: Path, name: str, text: str) -> str:
    out.mkdir(parents=True, exist_ok=True)
    (out / (name + '.java')).write_text(text)
    stub = out / 'android/util/Log.java';stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text('package android.util; public class Log { public static int w(String t,String m){return 0;} }')
    subprocess.run(['javac','--release','8','-d',str(out),str(stub),str(out/(name+'.java'))],check=True)
    result=subprocess.run(['java','-cp',str(out),name],check=True,capture_output=True,text=True,timeout=30)
    print(result.stdout.strip());return result.stdout.strip()


def run(before: Path, after: Path, out: Path) -> None:
    old=(before/LIVE).read_text();new=(after/LIVE).read_text()
    assert digest(old.encode())==RC2_SHA
    assert new==transform(old), 'Unexpected edits outside exact lifecycle transform'
    # Full Android packaging tree preservation, when supplied by CI.
    if (before/GRADLE).exists():
        def inventory(root):
            paths=list((root/'tools/android/packaging/xbmc').rglob('*'))+[root/'cmake/scripts/android/Install.cmake']
            return {str(p.relative_to(root)):p.read_bytes() for p in paths if p.is_file()}
        a,b=inventory(before),inventory(after)
        # --after in CI points at the full Kodi tree; compare the preimage's scope only.
        keys=set(a)|{k for k in b if k.startswith('tools/android/packaging/xbmc/') or k=='cmake/scripts/android/Install.cmake'}
        changed={k for k in keys if a.get(k)!=b.get(k)}
        assert changed=={str(LIVE),str(GRADLE)},changed
    protected=('onResume','onPause','onStop','onConfigurationChanged','onMultiWindowModeChanged',
               'onUserLeaveHint','onPictureInPictureModeChanged','returnToInfinity',
               'configureCobraPip','enterCobraPictureInPicture','startCobraPlayer',
               'rememberAndPauseCobraPlayer','isCurrentCobraPlayer','pauseCobraForBackground','resumeCobraAfterBackground')
    for name in protected:
        assert method(old,name)==method(new,name).replace('postCobraDelayed(', 'mMain.postDelayed('),name
    assert new.count('mIo.execute(')==1 and new.count('mMain.postDelayed(')==1
    assert 'runOnUiThread(' not in new and new.count('postCobraUi(')==11
    oldh=PREFIX+'public class OldGuideTest extends Parent {\n'+FIELDS+method(old,'loadGuideAsync')+r'''
 public static void main(String[] args){OldGuideTest a=new OldGuideTest();a.mIo=Executors.newSingleThreadExecutor();a.mIo.shutdownNow();
  try{a.loadGuideAsync(new LiveSource());throw new AssertionError("RC2 crash not reproduced");}
  catch(RejectedExecutionException expected){System.out.println("PASS: exact RC2 loadGuideAsync reproduces terminated-executor crash");}}
}'''
    reproduced=compile_run(out/'rc2-reproduction','OldGuideTest',oldh)
    names=('isCobraAsyncAlive','submitCobraIo','postCobraUi','postCobraDelayed','stopCobraAsync','onDestroy','loadGuideAsync')
    bodies='\n'.join(method(new,n) for n in names)
    newh=PREFIX+'public class GateTest extends Parent {\n'+FIELDS+r'''
 private volatile boolean mAsyncDestroyed;private final Object mAsyncLock=new Object();
 Runnable mAutoRefresh=()->{},mStallWatchdog=()->{},mProgressTicker=()->{},mHideMultiChrome=()->{};
 class DeviceBridge {void close(){}}DeviceBridge mDeviceBridge=new DeviceBridge();int releaseSawDead;
 void releaseSinglePlayer(){if(mAsyncDestroyed)releaseSawDead++;}
 void releaseMulti(){if(mAsyncDestroyed)releaseSawDead++;}
 GateTest(ExecutorService io){mIo=io;}
'''+bodies+TESTS
    tested=compile_run(out/'rc3-behavior','GateTest',newh)
    report={'rc2_reproduction':reproduced,'rc3_behavior':tested,'protected_methods':len(protected),
            'io_routes':6,'ui_callbacks':10,'delayed_routes':11,'source_transform_exact':True,
            'android_device_tested':False}
    (out/'lifecycle-test-report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.before,a.after,a.out)
