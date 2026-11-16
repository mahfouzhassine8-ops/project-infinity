"""Host checks of exact open() admission ordering; no Android or native execution."""
from pathlib import Path
import hashlib
import json
import subprocess
import test_bridge_restored as common


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / 'java/com/projectinfinity/kodi/InfinityVideoLockBridge.java'
HARNESS = r'''
package com.projectinfinity.kodi;
public final class InfinityVideoLockBridge {
  static final int ENTRY_FAILED=6;
  static final Queue UI=new Queue();
  static InfinityVideoLockBridge current;
  static int failures,checks;static long failedToken;
  final Main owner;final long session;final DialogAdapter dialog=new DialogAdapter();
  int theme,refreshes,attached,disposals;
  InfinityVideoLockBridge(Main owner,long session,int theme){this.owner=owner;this.session=session;this.theme=theme;}
  static boolean eligible(Main owner){return owner!=null&&owner.eligible;}
  static boolean inPip(Main owner){return owner.pip;}
  static boolean transition(long token,int operation,long epoch,long request){if(token>0){failures++;failedToken=token;}return true;}
  void refreshViewport(){refreshes++;}
  void attachViewport(){attached++;}
  void dispose(boolean notify){disposals++;if(current==this)current=null;}
__ACTUAL_OPEN__
  static final class Main {static Main MainActivity;boolean eligible,pip;View mMainView=new View();}
  static final class View {boolean attached=true;int width=100,height=200;boolean isAttachedToWindow(){return attached;}int getWidth(){return width;}int getHeight(){return height;}}
  static final class DialogAdapter {boolean foreground,pip,locked;void setForeground(boolean v){foreground=v;}void setPictureInPicture(boolean v){pip=v;}boolean lock(long token){locked=true;return true;}}
  static final class Queue {final java.util.ArrayDeque<Runnable> items=new java.util.ArrayDeque<>();void post(Runnable r){items.add(r);}void drain(){while(!items.isEmpty())items.remove().run();}}
  static void check(boolean value,String label){checks++;if(!value)throw new AssertionError(label);}
  static Main fresh(){failures=0;failedToken=0;current=null;Main m=new Main();Main.MainActivity=m;return m;}
  public static void main(String[]args){
    Main owner=fresh();InfinityVideoLockBridge established=current=new InfinityVideoLockBridge(owner,100,0);
    owner.eligible=false;owner.mMainView=null;open(100,1);UI.drain();
    check(current==established&&established.disposals==0&&failures==0,"Established background entry never reports initial abort or disposes owner");
    check(!established.dialog.foreground&&established.theme==1&&established.refreshes==1,"Established background refresh keeps Dialog out of foreground");
    owner.eligible=true;owner.mMainView=new View();open(100,0);UI.drain();
    check(current==established&&established.dialog.foreground&&failures==0,"Same established session can return to foreground");
    owner=fresh();InfinityVideoLockBridge newer=current=new InfinityVideoLockBridge(owner,101,0);
    owner.eligible=false;open(100,1);UI.drain();
    check(failures==1&&failedToken==100,"Ineligible different token reports only that token's entry failure");
    check(current==newer&&newer.disposals==0&&newer.theme==0,"Ineligible old entry cannot mutate newer session");
    owner=fresh();owner.eligible=true;owner.mMainView.attached=false;
    open(102,0);UI.drain();check(current==null&&failures==1&&failedToken==102,"New detached-view entry fails without creating controller");
    owner=fresh();owner.eligible=true;owner.mMainView.width=0;
    open(103,0);UI.drain();check(current==null&&failures==1,"New zero-width entry fails before controller creation");
    owner=fresh();owner.eligible=true;open(104,1);UI.drain();
    check(current!=null&&current.session==104&&current.owner==owner&&current.dialog.locked&&current.dialog.foreground,"Eligible new entry creates and locks correct owner");
    check(current.attached==1&&current.refreshes==1&&failures==0,"Eligible new entry attaches viewport before locking");
    System.out.println("PASS actual Bridge.open "+checks+" assertions");
  }
}
'''


def main():
    source = BRIDGE.read_text()
    method = common.extract_method(source.replace('  public static void open(', '  public static void restored(', 1))
    method = method.replace('  public static void restored(', '  public static void open(', 1)
    assert method in source, 'Extracted production method must be byte-identical'
    work = Path('/tmp/infinity502-lock-open-host'); work.mkdir(exist_ok=True)
    harness = work / 'InfinityVideoLockBridge.java'; harness.write_text(HARNESS.replace('__ACTUAL_OPEN__', method))
    compiler = Path('/workspace/scratch/network-baseline-2103477/ecj-3.37.0.jar')
    compile_result = subprocess.run(['java', '-jar', str(compiler), '-17', '-d', str(work / 'classes'), str(harness)], text=True, capture_output=True)
    run = None
    if compile_result.returncode == 0:
        run = subprocess.run(['java', '-cp', str(work / 'classes'), 'com.projectinfinity.kodi.InfinityVideoLockBridge'], text=True, capture_output=True)
    passed = compile_result.returncode == 0 and run is not None and run.returncode == 0
    report = {'status': 'PASS_ACTUAL_OPEN_METHOD_HOST_CHECKS' if passed else 'FAIL',
              'bridge_sha256': hashlib.sha256(source.encode()).hexdigest(), 'open_method_sha256': hashlib.sha256(method.encode()).hexdigest(),
              'compile_exit_code': compile_result.returncode, 'compile_output': compile_result.stdout + compile_result.stderr,
              'test_exit_code': None if run is None else run.returncode, 'test_output': '' if run is None else run.stdout + run.stderr,
              'scope': 'Actual open method with queue/owner/viewport adapters; admission-order effects only',
              'state_128_and_ACK_16': 'NOT_RERUN', 'actual_Android': 'NOT_RUN', 'shutdown': 'NOT_RUN'}
    (ROOT / 'BRIDGE-OPEN-TEST.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status']);print(report['compile_output'], end='');print(report['test_output'], end='')
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
