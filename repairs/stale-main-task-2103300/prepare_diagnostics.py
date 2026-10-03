#!/usr/bin/env python3
"""Prepare inherited Android compile/tests and add the stale-task regression."""
from pathlib import Path
import argparse
import subprocess
import sys

HERE = Path(__file__).resolve().parent

OLD = '''  @Test public void launcherFlagsCannotResetLiveMainAndDeepLinkGrantsSurvive(){
    ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();
    Intent incoming=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("content://test/movie"));
    incoming.putExtra("preserved","yes");incoming.addFlags(Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|Intent.FLAG_ACTIVITY_CLEAR_TASK|
        Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_MULTIPLE_TASK|Intent.FLAG_GRANT_READ_URI_PERMISSION);
    for(boolean live:new boolean[]{false,true}){
      Intent target=InfinityStartupHandoff.mainIntent(c.get(),incoming,live);
      assertEquals(Main.class.getName(),target.getComponent().getClassName());assertEquals(incoming.getData(),target.getData());
      assertEquals("yes",target.getStringExtra("preserved"));assertEquals(Intent.ACTION_VIEW,target.getAction());
      int f=target.getFlags();assertEquals(0,f&(Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|Intent.FLAG_ACTIVITY_CLEAR_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_MULTIPLE_TASK));
      assertTrue((f&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);assertTrue((f&Intent.FLAG_ACTIVITY_SINGLE_TOP)!=0);
      assertEquals(live,(f&Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)!=0);
    }
    c.pause().stop().destroy();
  }'''

NEW = '''  @Test public void staleSingleInstanceTaskIsClearedOnlyForFreshMainAndLiveMainIsReused(){
    ActivityController<Activity> c=Robolectric.buildActivity(Activity.class).setup();
    Intent incoming=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("content://test/movie"));
    incoming.putExtra("preserved","yes");incoming.addFlags(Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|Intent.FLAG_ACTIVITY_CLEAR_TASK|
        Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_MULTIPLE_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP|
        Intent.FLAG_GRANT_READ_URI_PERMISSION);
    for(boolean live:new boolean[]{false,true}){
      Intent target=InfinityStartupHandoff.mainIntent(c.get(),incoming,live);
      assertEquals(Main.class.getName(),target.getComponent().getClassName());assertEquals(incoming.getData(),target.getData());
      assertEquals("yes",target.getStringExtra("preserved"));assertEquals(Intent.ACTION_VIEW,target.getAction());
      int f=target.getFlags();
      assertEquals(0,f&(Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED|Intent.FLAG_ACTIVITY_CLEAR_TOP|
          Intent.FLAG_ACTIVITY_MULTIPLE_TASK|Intent.FLAG_ACTIVITY_NEW_DOCUMENT|Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP));
      assertTrue((f&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0);assertTrue((f&Intent.FLAG_ACTIVITY_NEW_TASK)!=0);
      if(live){
        assertEquals(0,f&Intent.FLAG_ACTIVITY_CLEAR_TASK);
        assertTrue((f&Intent.FLAG_ACTIVITY_SINGLE_TOP)!=0);assertTrue((f&Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)!=0);
      }else{
        assertTrue((f&Intent.FLAG_ACTIVITY_CLEAR_TASK)!=0);
        assertEquals(0,f&(Intent.FLAG_ACTIVITY_SINGLE_TOP|Intent.FLAG_ACTIVITY_REORDER_TO_FRONT));
      }
    }
    c.pause().stop().destroy();
  }'''

def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(f'Expected one lifecycle test preimage, found {text.count(old)}')
    return text.replace(old, new, 1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    a = p.parse_args()
    subprocess.run([sys.executable, str(HERE.parent/'graceful-exit-handoff-2103299/prepare_diagnostics.py'),
                    '--root',str(a.root),'--build',str(a.build),'--evidence',str(a.evidence)], check=True)
    test = a.build/'xbmc/src/test/java/com/projectinfinity/kodi/StartupLifecycleTest.java'
    test.write_text(once(test.read_text(), OLD, NEW))
    print('PASS: Android test source now requires CLEAR_TASK for stale single-instance Main only')

if __name__ == '__main__':
    main()
