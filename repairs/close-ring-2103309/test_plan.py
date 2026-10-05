#!/usr/bin/env python3
"""Run the transformed production Plan without loading Android or native Kodi."""
import argparse
import subprocess
import tempfile
from pathlib import Path
from apply import PREFIX,transform_exit

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    s=transform_exit((a.source/(PREFIX+'InfinityExitCompletion.java.in')).read_text())
    block=s[s.index('  private static volatile Plan observedClosePlan;'):s.index('  static boolean requestNormal(Main owner)')]
    fixture='''
class SystemClock { static long now; static long elapsedRealtime(){return now;} }
class InfinityExitCompletion { static final long STALL_BOUND_MS=15000;
'''+block+'''
}
class PlanCheck {
  static void check(boolean value){if(!value)throw new AssertionError();}
  public static void main(String[] args){
    var first=new InfinityExitCompletion.Plan();check(first.requestNormal());check(!first.requestNormal());
    check(!first.stopped(true));check(first.stopped(false));check(!first.stopped(false));
    first.destroying();SystemClock.now=300000;check(first.stalled(SystemClock.now));
    check(InfinityExitCompletion.closePhase()==InfinityExitCompletion.Plan.Phase.DESTROYING);
    first.completed();check(InfinityExitCompletion.closePhase()==InfinityExitCompletion.Plan.Phase.COMPLETE);
    var old=new InfinityExitCompletion.Plan();old.requestNormal();
    var current=new InfinityExitCompletion.Plan();current.requestNormal();current.stopped(false);
    old.destroying();old.completed();check(InfinityExitCompletion.closePhase()==InfinityExitCompletion.Plan.Phase.QUIT_QUEUED);
    current.destroying();current.completed();
    var canceled=new InfinityExitCompletion.Plan();canceled.requestNormal();check(canceled.cancelBeforeQuit());
    check(InfinityExitCompletion.closePhase()==InfinityExitCompletion.Plan.Phase.RUNNING);
    var forced=new InfinityExitCompletion.Plan();forced.requestNormal();check(forced.force());forced.destroying();forced.completed();
    check(InfinityExitCompletion.closePhase()==InfinityExitCompletion.Plan.Phase.FORCED);
    var external=new InfinityExitCompletion.Plan();external.destroying();
    check(InfinityExitCompletion.closePhase()==InfinityExitCompletion.Plan.Phase.DESTROYING);
    external.completed();check(InfinityExitCompletion.closePhase()==InfinityExitCompletion.Plan.Phase.COMPLETE);
    System.out.println("PASS: production close phases, native-return boundary, timeout, cancellation, force and late-owner ordering");
  }
}
'''
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary);(root/'PlanCheck.java').write_text(fixture)
        subprocess.run(['javac',str(root/'PlanCheck.java')],check=True)
        subprocess.run(['java','-cp',str(root),'PlanCheck'],check=True)

if __name__=='__main__':main()
