#!/usr/bin/env python3
"""Compile the actual three player callback statements with deterministic Java stubs.

This is an offline callback regression, not an Android touch/phone test.
Full activity compilation and native-payload preservation are separate CI gates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from apply import LIVE, OLD_HOLD, NEW_HOLD

HARNESS = r'''
public final class VideoHoldHarness {
  static final class View {
    interface Click { void onClick(View v); }
    interface Hold { boolean onLongClick(View v); }
    interface Key { boolean onKey(View v, int code, KeyEvent e); }
    Click click; Hold hold; Key key;
    void setOnClickListener(Click x){click=x;}
    void setOnLongClickListener(Hold x){hold=x;}
    void setOnKeyListener(Key x){key=x;}
  }
  static final class KeyEvent {
    static final int ACTION_DOWN=0, ACTION_UP=1, KEYCODE_DPAD_CENTER=23, KEYCODE_ENTER=66, KEYCODE_MENU=82;
    final int action;
    KeyEvent(int action){this.action=action;}
    int getAction(){return action;}
  }
  View mPlayerOverlay;
  boolean mCobraPlayerLocked, sheet, drawer, multi;
  int menus, unlocks, toggles, chrome;
  static int assertions;
  void showCobraPlayerDrawer(){menus++;drawer=true;}
  void showCobraPlayerUnlockAffordance(){unlocks++;}
  void togglePlayerChrome(){toggles++;}
  void showPlayerChromeTemporarily(){chrome++;}
  boolean closeCobraActionSheet(){boolean was=sheet;sheet=false;return was;}
  boolean closeCobraPlayerDrawer(){boolean was=drawer;drawer=false;return was;}
  boolean closeCobraMultiPicker(boolean ignored){boolean was=multi;multi=false;return was;}
  void bind(){
    mPlayerOverlay=new View();
    // EXACT_CALLBACKS
  }
  static VideoHoldHarness fresh(){VideoHoldHarness x=new VideoHoldHarness();x.bind();return x;}
  static void check(boolean ok,String label){assertions++;if(!ok)throw new AssertionError(label);}
  boolean key(int code,int action){return mPlayerOverlay.key.onKey(mPlayerOverlay,code,new KeyEvent(action));}
  boolean hold(){return mPlayerOverlay.hold.onLongClick(mPlayerOverlay);}
  void tap(){mPlayerOverlay.click.onClick(mPlayerOverlay);}
  boolean noEffects(){return menus==0&&unlocks==0&&toggles==0&&chrome==0;}
  public static void main(String[] args){
    VideoHoldHarness x=fresh();
    check(x.hold(),"hold consumed to prevent fallback context/tap");
    check(x.noEffects(),"unlocked video hold has no UI action");
    x.mCobraPlayerLocked=true;
    check(x.hold(),"locked hold consumed");
    check(x.noEffects(),"locked background hold does not open a menu or unlock");
    x=fresh(); boolean all=true;for(int i=0;i<100;i++)all &= x.hold();
    check(all&&x.noEffects(),"repeated holds remain inert");
    x.tap();check(x.toggles==1&&x.menus==0,"tap after holds toggles controls normally");
    x=fresh();x.tap();check(x.toggles==1,"single tap preserved");
    x=fresh();x.sheet=true;x.tap();check(!x.sheet&&x.toggles==0&&x.menus==0,"tap dismisses action sheet");
    x=fresh();x.drawer=true;x.tap();check(!x.drawer&&x.toggles==0,"tap dismisses channel drawer");
    x=fresh();x.multi=true;x.tap();check(!x.multi&&x.toggles==0,"tap dismisses picker");
    x=fresh();x.mCobraPlayerLocked=true;x.tap();check(x.unlocks==1&&x.menus==0,"locked tap reveals unlock affordance");
    x=fresh();check(x.key(KeyEvent.KEYCODE_MENU,0)&&x.menus==1,"explicit MENU key preserved");
    x=fresh();check(x.key(KeyEvent.KEYCODE_DPAD_CENTER,0)&&x.chrome==1&&x.menus==0,"center key reveals chrome");
    x=fresh();check(x.key(KeyEvent.KEYCODE_ENTER,0)&&x.chrome==1&&x.menus==0,"enter key reveals chrome");
    x=fresh();check(!x.key(KeyEvent.KEYCODE_MENU,1)&&x.noEffects(),"key-up ignored");
    x=fresh();check(!x.key(99,0)&&x.noEffects(),"unhandled key preserved");
    x=fresh();x.mCobraPlayerLocked=true;check(x.key(KeyEvent.KEYCODE_MENU,0)&&x.unlocks==1&&x.menus==0,"locked key cannot open menu");
    x=fresh();x.drawer=true;check(x.hold()&&x.drawer&&x.noEffects(),"hold does not toggle existing drawer");
    System.out.println("PASS: "+assertions+" actual-callback assertions; Android input dispatch not simulated");
  }
}
'''


def run(source: Path, evidence: Path) -> dict:
    before = (evidence/'InfinityLiveActivity-before.java.in').read_text()
    after = (source/LIVE).read_text()
    if before.count(OLD_HOLD)!=1 or after!=before.replace(OLD_HOLD,NEW_HOLD,1):
        raise AssertionError('The entire Activity must differ by ONLY the reviewed listener replacement')
    # All other listeners, the toolbar, seek code, players and full-screen entry paths are consequently exact.
    prefixes = ('mPlayerOverlay.setOnClickListener(', 'mPlayerOverlay.setOnLongClickListener(', 'mPlayerOverlay.setOnKeyListener(')
    callbacks=[]
    for prefix in prefixes:
        lines=[line.strip() for line in after.splitlines() if line.strip().startswith(prefix)]
        if len(lines)!=1:
            raise AssertionError('Unexpected callback inventory: '+prefix)
        callbacks.append(lines[0])
    text=HARNESS.replace('// EXACT_CALLBACKS','\n    '.join(callbacks))
    harness=evidence/'VideoHoldHarness.java'
    harness.write_text(text)
    classes=evidence/'harness-classes';classes.mkdir()
    subprocess.run(['javac','-d',str(classes),str(harness)],check=True,timeout=45)
    result=subprocess.run(['java','-cp',str(classes),'VideoHoldHarness'],check=True,
        capture_output=True,text=True,timeout=30)
    if 'PASS: 18 actual-callback assertions' not in result.stdout:
        raise AssertionError('Harness did not finish all assertions')
    (evidence/'gesture-tests.txt').write_text(result.stdout)
    proof={'source_diff_exact':True,'java_callback_assertions':18,
        'other_activity_code_byte_identical':True,
        'candidate_activity_sha256':hashlib.sha256(after.encode()).hexdigest(),
        'device_tested':False,'android_touch_dispatch_tested':False}
    (evidence/'gesture-tests.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(result.stdout,end='')
    return proof


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    run(args.source.resolve(),args.evidence.resolve())
