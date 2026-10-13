#!/usr/bin/env python3
"""Compile the exact saved task-retirement method against controlled Java peers.

This is NOT an Android/Robolectric test. It exposes one deterministic interleaving
in actual saved production logic. A reproduced counterexample FAILS the release
gate: the harness saves its receipt and exits 1 after observing it.
Usage: python tests/reproduce_recents_race.py [path/to/InfinityCloseGuardService.java.in]
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

BASE=Path(__file__).resolve().parents[1]
EXPECTED='790209e1d00f106e8f054fcdaf3dc92f28acc59199ffa42eb6bb6aaca28b79a0'
MARKER='private String retireConfirmedClosedKodiTask(Session completed)'

def method(source):
    start=source.index(MARKER); opening=source.index('{',start); depth=1; end=opening+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}'); end+=1
    return source[start:end]

PEERS=r'''
import java.io.File;
import java.util.*;
public final class RecentsRaceHarness {
  String phase="COMPLETE"; boolean checkpointSaved=true,consumed=true,revoked=false,ended=false;
  Session session=new Session(); ActivityManager manager=new ActivityManager();
  static final String ACTIVITY_SERVICE="activity";
  static final class Session {int pid=111,taskId=71;String owner="closed-owner";}
  static final class Main {}
  static final class Build {static final class VERSION {static int SDK_INT=35;}}
  static final class ComponentName {
    String getPackageName(){return "com.projectinfinity.kodi";}
    String getClassName(){return Main.class.getName();}
  }
  static final class Intent {ComponentName getComponent(){return new ComponentName();}}
  static final class ActivityManager {
    AppTask task=new AppTask();
    List<AppTask> getAppTasks(){return Collections.singletonList(task);}
    static final class RecentTaskInfo {int taskId=71,persistentId=71;ComponentName baseActivity=new ComponentName();Intent baseIntent=new Intent();}
    static final class AppTask {
      boolean removed=false,removedWhileReplacementLive=false;Runnable duringLookup;
      RecentTaskInfo getTaskInfo(){if(duringLookup!=null){duringLookup.run();duringLookup=null;}return new RecentTaskInfo();}
      void finishAndRemoveTask(){removed=true;removedWhileReplacementLive=InfinityKodiShutdown.current.alive;}
    }
  }
  static final class InfinityKodiShutdown {
    static Snapshot current;static int retirementChecks;static boolean injectAfterLastObservation;
    interface Life{boolean alive(int pid,String owner);}
    static final class Snapshot {
      final int pid;final String owner;final boolean alive;
      Snapshot(int p,String o,boolean a){pid=p;owner=o;alive=a;}
      static Snapshot empty(){return new Snapshot(0,"",false);}
    }
    static Snapshot read(File d,Life life,Snapshot empty){return current;}
    static boolean ownerAlive(File d,int pid,String owner){return current.pid==pid&&current.owner.equals(owner)&&current.alive;}
    static boolean ownerRetired(File d,int pid,String owner){
      ++retirementChecks;
      // Old owner's lease remains retired. A different owner can publish after
      // the last snapshot while the guard still authorizes the old task ID.
      if(injectAfterLastObservation&&retirementChecks==2) replacement();
      return true;
    }
    static void replacement(){current=new Snapshot(222,"replacement-owner",true);}
    static void reset(){current=new Snapshot(111,"closed-owner",false);retirementChecks=0;injectAfterLastObservation=false;}
  }
  File getFilesDir(){return new File(".");}
  String getPackageName(){return "com.projectinfinity.kodi";}
  Object getSystemService(String type){return manager;}
  static void require(boolean passed,String detail){if(!passed)throw new AssertionError(detail);}
  static RecentsRaceHarness fresh(){InfinityKodiShutdown.reset();return new RecentsRaceHarness();}
  public static void main(String[] args){
    RecentsRaceHarness h=fresh();
    require(h.retireConfirmedClosedKodiTask(h.session).equals("removed_confirmed_closed_main_task"),"normal close control");
    require(h.manager.task.removed&&!h.manager.task.removedWhileReplacementLive,"dead owner control");
    h=fresh();InfinityKodiShutdown.replacement();h.retireConfirmedClosedKodiTask(h.session);
    require(!h.manager.task.removed,"replacement before observation must be preserved");
    h=fresh();h.manager.task.duringLookup=InfinityKodiShutdown::replacement;h.retireConfirmedClosedKodiTask(h.session);
    require(!h.manager.task.removed,"existing during-lookup correction must be preserved");
    h=fresh();h.phase="CHECKPOINT_FAILED";h.retireConfirmedClosedKodiTask(h.session);
    require(!h.manager.task.removed,"failed checkpoint must not remove a task");
    h=fresh();h.phase="RUNNING";h.retireConfirmedClosedKodiTask(h.session);
    require(!h.manager.task.removed,"normal background must not remove a task");
    h=fresh();InfinityKodiShutdown.injectAfterLastObservation=true;
    String result=h.retireConfirmedClosedKodiTask(h.session);
    require(h.manager.task.removedWhileReplacementLive,"expected saved-source race did not reproduce");
    System.out.println("CONTROL_CASES=5");
    System.out.println("COUNTEREXAMPLE=replacement_after_last_snapshot_removed");
    System.out.println("METHOD_RESULT="+result);
    System.out.println("RELEASE_GATE=FAIL");
    System.out.println("SCOPE=actual_method_with_controlled_peers_not_Android_OS");
  }
}
'''

def main():
    if len(sys.argv)>1:
        raw=Path(sys.argv[1]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=EXPECTED:
            raise SystemExit('Source hash mismatch; refusing to attribute this run to the saved candidate.')
        fragment=method(raw.decode())
    else:
        fragment=(BASE/'evidence/task-retirement-method.java.txt').read_text()
        receipt=json.loads((BASE/'evidence/recents-source.json').read_text())
        if hashlib.sha256(fragment.encode()).hexdigest()!=receipt['method_sha256']:
            raise SystemExit('Extracted method hash mismatch.')
    source=PEERS.replace('  static void require(', '  '+fragment+'\n  static void require(',1)
    with tempfile.TemporaryDirectory() as temporary:
        folder=Path(temporary);(folder/'RecentsRaceHarness.java').write_text(source)
        subprocess.run(['javac','-Xlint:all','-Werror','--release','11','RecentsRaceHarness.java'],cwd=folder,check=True)
        result=subprocess.run(['java','-ea','-cp',str(folder),'RecentsRaceHarness'],check=True,capture_output=True,text=True)
    print(result.stdout,end='')
    (BASE/'evidence/recents-race.log').write_text(result.stdout)
    (BASE/'evidence/recents-race.json').write_text(json.dumps({
        'source_sha256':EXPECTED,'compiled_method_sha256':hashlib.sha256(fragment.encode()).hexdigest(),
        'harness_completed':True,'controls_passed':5,
        'replacement_counterexample_reproduced':True,'release_gate':'FAIL',
        'production_runtime_changed':False,'android_os_test':False,'physical_device_test':False,
        'scope':'Exact saved production method compiled with controlled Java peers. No Android SDK or native engine compilation.'
    },indent=2)+'\n')

if __name__=='__main__':
    main()
    # The pinned candidate remains unsafe under the reproduced interleaving.
    raise SystemExit(1)
