#!/usr/bin/env python3
"""Run actual task-intent and close-presentation code with narrow host API peers.

These checks cover route/flag/state decisions; Android task placement, PiP and
native playback are physical-device/Android integration checks, not host passes.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
SRC = HERE/'runtime/android/overlay/tools/android/packaging/xbmc/src'
MANIFEST = HERE/'runtime/android/overlay/tools/android/packaging/xbmc/AndroidManifest.xml.in'

def block(text, marker):
    start=text.index(marker); opening=text.index('{',start); depth=1; end=opening+1
    # These production blocks have no brace-bearing strings or comments.
    while depth:
        depth += (text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]

class LifecycleTests(unittest.TestCase):
    def test_actual_snapshot_and_intent_decisions(self):
        state=block((SRC/'InfinityKodiShutdown.java.in').read_text(),'static final class Snapshot')
        home=block((SRC/'InfinityCloseGuardService.java.in').read_text(),'static Intent homeIntent()')
        handoff=block((SRC/'InfinityStartupHandoff.java.in').read_text(),'static Intent mainIntent(')
        peers='''
import java.util.*;
class SystemClock {static long elapsedRealtime(){return 100000;}}
class InfinityExitCompletion {static class Plan {enum Phase {RUNNING,QUIESCE,PERSISTING,CHECKPOINT_FAILED,COMPLETE,FORCED}}}
class InfinityCloseProgress {static Display display;static class Display {long started;boolean matches(int p,String o){return false;}}}
class Activity {} class Main extends Activity {}
class Intent {
 static final String ACTION_MAIN="main",CATEGORY_HOME="home";
 static final int FLAG_ACTIVITY_RESET_TASK_IF_NEEDED=1,FLAG_ACTIVITY_CLEAR_TASK=2,
 FLAG_ACTIVITY_CLEAR_TOP=4,FLAG_ACTIVITY_MULTIPLE_TASK=8,FLAG_ACTIVITY_NEW_DOCUMENT=16,
 FLAG_ACTIVITY_PREVIOUS_IS_TOP=32,FLAG_ACTIVITY_REORDER_TO_FRONT=64,
 FLAG_ACTIVITY_SINGLE_TOP=128,FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS=256,
 FLAG_ACTIVITY_NEW_TASK=512,FLAG_GRANT_READ_URI_PERMISSION=1024;
 int flags;String action;Class<?> target;Set<String> categories=new HashSet<>();String content;
 Intent(){}Intent(String a){action=a;}Intent(Intent i){flags=i.flags;action=i.action;target=i.target;categories.addAll(i.categories);content=i.content;}
 Intent setClass(Activity a,Class<?> c){target=c;return this;}int getFlags(){return flags;}
 Intent setFlags(int f){flags=f;return this;}Intent addFlags(int f){flags|=f;return this;}
 Intent addCategory(String c){categories.add(c);return this;}
}
'''
        checks='''
 static void check(boolean yes,String why){if(!yes)throw new AssertionError(why);}
 public static void main(String[] args){
  Snapshot failed=new Snapshot(42,"owner","launch","save failed",1,2,InfinityExitCompletion.Plan.Phase.CHECKPOINT_FAILED,true,false,false);
  check(failed.pending(),"failed live owner may not be relaunched");
  check(failed.stalled()&&failed.checkpointFailed(),"failure must expose recovery immediately");
  check(failed.closeTitle().contains("failed")&&!failed.closeNotice().contains("finishing"),"failed close described as progress");
  check(!failed.complete&&failed.closeMessage().contains("Waiting will not"),"failure fabricated completion or wait promise");
  Snapshot running=new Snapshot(42,"owner","launch","",1,2,InfinityExitCompletion.Plan.Phase.PERSISTING,true,false,false);
  check(running.pending()&&!running.checkpointFailed()&&running.closeNotice().contains("finishing"),"saving presentation changed");
  Snapshot dead=new Snapshot(42,"owner","launch","save failed",1,2,InfinityExitCompletion.Plan.Phase.CHECKPOINT_FAILED,false,false,false);
  check(!dead.pending()&&!dead.stalled()&&!dead.complete,"dead failed owner falsely blocks launch or confirms save");
  Snapshot complete=new Snapshot(42,"owner","launch","",1,2,InfinityExitCompletion.Plan.Phase.COMPLETE,false,false,true);
  check(!complete.pending()&&!complete.checkpointFailed(),"confirmed close blocked");
  Intent destination=homeIntent();
  check(Intent.ACTION_MAIN.equals(destination.action)&&destination.categories.contains(Intent.CATEGORY_HOME)&&destination.target==null,"Close opened an app activity");
  check(destination.flags==Intent.FLAG_ACTIVITY_NEW_TASK,"Home intent includes destructive flags");
  Intent input=new Intent("view").setFlags(Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS|Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|Intent.FLAG_GRANT_READ_URI_PERMISSION);input.content="content://movie";
  for(boolean live:new boolean[]{false,true}){
   Intent target=mainIntent(new Activity(),input,live);
   check((target.flags&Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS)==0,"Main excluded from Recents");
   check((target.flags&Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED)==0,"launcher reset inherited");
   check((target.flags&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0&&"content://movie".equals(target.content),"deep-link grant/content lost");
   check(target.target==Main.class,"wrong target");
   check(((target.flags&Intent.FLAG_ACTIVITY_CLEAR_TASK)!=0)==!live,"valid live Main cleared or stale task retained");
  }
  check((input.flags&Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS)!=0,"incoming intent mutated");
  System.out.println("PASS actual close-state presentation, owner gating, Home route and fresh/live Main flags");
 }
'''
        with tempfile.TemporaryDirectory(prefix='infinity-close-lifecycle-') as folder:
            root=Path(folder);java=root/'LifecycleRuntimeTest.java'
            java.write_text(peers+'public class LifecycleRuntimeTest {\n'+state+'\n'+home+'\n'+handoff+'\n'+checks+'\n}')
            subprocess.run(['java','com.sun.tools.javac.Main','--release','8','-d',str(root),str(java)],check=True)
            subprocess.run(['java','-ea','-cp',str(root),'LifecycleRuntimeTest'],check=True)

    def test_manifest_preserves_other_activities_and_kodi_process(self):
        ns='{http://schemas.android.com/apk/res/android}'
        manifest=ET.parse(MANIFEST).getroot();activities={n.attrib[ns+'name']:n for n in manifest.find('application').findall('activity')}
        main=activities['.Main'].attrib
        self.assertEqual(main[ns+'process'],':kodi')
        self.assertEqual(main[ns+'launchMode'],'singleInstance')
        self.assertEqual(main[ns+'taskAffinity'],'@APP_PACKAGE@.infinity.kodi')
        self.assertEqual(main[ns+'excludeFromRecents'],'false')
        self.assertEqual(main[ns+'finishOnTaskLaunch'],'false')
        self.assertEqual(main[ns+'supportsPictureInPicture'],'true')
        self.assertEqual(activities['.InfinityKodiEntryActivity'].attrib[ns+'excludeFromRecents'],'true')
        self.assertNotIn(ns+'taskAffinity',activities['.InfinityLiveActivity'].attrib)

    def test_close_guard_keeps_authorization_and_notification_recovery(self):
        guard=(SRC/'InfinityCloseGuardService.java.in').read_text()
        startup=block(guard,'@Override public int onStartCommand(')
        self.assertIn('startActivity(homeIntent())',startup)
        self.assertNotIn('new Intent(this,Splash.class)',startup)
        self.assertIn('new Intent(this,Splash.class)',block(guard,'private Notification notice('))
        endpoint=(SRC/'InfinityCloseNativeLease.java.in').read_text()
        self.assertEqual(endpoint.count('android.os.Process.killProcess('),1)
        self.assertIn('if(owner.infinityAuthorizeCheckpointTermination',endpoint)
        self.assertIn('consumeGuard(generation,proof)',endpoint)

if __name__=='__main__':unittest.main()
