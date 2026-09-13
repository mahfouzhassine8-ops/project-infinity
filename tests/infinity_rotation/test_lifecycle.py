#!/usr/bin/env python3
"""Exercise the actual generated Java rotation owner with deterministic platform doubles.

This checks lifecycle dispatch and policy transitions, not Android device behavior.
The separate SDK gate compiles the complete real Main and checks JNI descriptors.
"""
import argparse
import re
import subprocess
from pathlib import Path


def methods(source, name):
    found = []
    pattern = r'  (?:private|public) (?:void|boolean) ' + name + r'\([^)]*\)\s*\{'
    for match in re.finditer(pattern, source):
        level, end = 1, match.end()
        while level:
            level += (source[end] == '{') - (source[end] == '}')
            end += 1
        found.append(source[match.start():end])
    assert found, name
    return found


def run(source, out):
    main = (source / 'tools/android/packaging/xbmc/src/Main.java.in').read_text()
    pause, = methods(main, 'onPause')
    assert pause.index('mPaused = true') < pause.index('infinityApplyPlayerRotation("pause")')
    resume, = methods(main, 'onResume')
    assert resume.index('mPaused = false') < resume.index('infinityApplyPlayerRotation("resume")')
    stop, = methods(main, 'onStop')
    assert 'SCREEN_ORIENTATION_UNSPECIFIED' in stop
    bodies = []
    for name in ('infinityHasActiveVideoSafely', 'infinityApplyPlayerRotation',
                 'infinityRequestPlayerOrientation', 'onPictureInPictureModeChanged',
                 'onMultiWindowModeChanged'):
        bodies += methods(main, name)
    out.mkdir(parents=True, exist_ok=True)
    config = out / 'android/content/res/Configuration.java'
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('package android.content.res; public class Configuration {}\n')
    java = r'''class Parent {
      public void onPictureInPictureModeChanged(boolean b) {}
      public void onPictureInPictureModeChanged(boolean b, android.content.res.Configuration c) {}
      public void onMultiWindowModeChanged(boolean b) {}
      public void onMultiWindowModeChanged(boolean b, android.content.res.Configuration c) {}
    }
    class ActivityInfo { static final int SCREEN_ORIENTATION_UNSPECIFIED=-1, SCREEN_ORIENTATION_FULL_SENSOR=10; }
    class Build { static class VERSION { static int SDK_INT=34; } }
    class Log { static void i(String a,String b) {} static void w(String a,String b,Throwable e) {} }
    public class RotationLifecycleTest extends Parent {
      static final String FEATURE_LEANBACK="leanback";
      static final int INFINITY_ROTATION_UNLOCKED=1;
      int mInfinityPlayerRotationMode=0;
      int mInfinityLastRequestedOrientation=Integer.MIN_VALUE;
      boolean mPaused=false,mInfinityDestroyed=false,pip=false,multi=false,tv=false,video=false;
      boolean reject=false,missingBridge=false,queryFailed=false;
      int requests=0,last=Integer.MIN_VALUE;
      class PM { boolean hasSystemFeature(String s) { return tv; } }
      PM getPackageManager() { return new PM(); }
      boolean isInPictureInPictureMode() { if(queryFailed) throw new IllegalStateException(); return pip; }
      boolean isInMultiWindowMode() { return multi; }
      boolean _infinityHasActiveVideo() { if(missingBridge) throw new UnsatisfiedLinkError(); return video; }
      void setRequestedOrientation(int v) { requests++; if(reject) throw new SecurityException(); last=v; }
      static void check(boolean v,String why) { if(!v) throw new AssertionError(why); }
    ''' + '\n'.join(bodies) + r'''
      public static void main(String[] args) {
        for(int mask=0;mask<256;mask++) {
          RotationLifecycleTest t=new RotationLifecycleTest();
          t.video=(mask&1)!=0; t.mInfinityPlayerRotationMode=(mask&2)!=0?1:0;
          t.mPaused=(mask&4)!=0; t.mInfinityDestroyed=(mask&8)!=0;
          t.tv=(mask&16)!=0; t.pip=(mask&32)!=0; t.multi=(mask&64)!=0;
          t.missingBridge=(mask&128)!=0;
          t.infinityApplyPlayerRotation("test");
          check(t.last==(mask==3?10:-1),"policy case "+mask);
        }
        RotationLifecycleTest t=new RotationLifecycleTest();
        t.video=true; t.mInfinityPlayerRotationMode=1;
        t.infinityApplyPlayerRotation("resume"); check(t.last==10,"fullscreen unlock");
        t.infinityApplyPlayerRotation("repeat"); check(t.requests==1,"deduplicate requests");
        t.pip=true; t.onPictureInPictureModeChanged(true,null); check(t.last==-1,"PiP release");
        t.pip=false; t.onPictureInPictureModeChanged(false,null); check(t.last==10,"PiP exit");
        t.multi=true; t.onMultiWindowModeChanged(true,null); check(t.last==-1,"multi-window release");
        t.multi=false; t.onMultiWindowModeChanged(false,null); check(t.last==10,"multi-window exit");
        Build.VERSION.SDK_INT=24;
        t.multi=true; t.onMultiWindowModeChanged(true); check(t.last==-1,"API24 release");
        t.multi=false; t.onMultiWindowModeChanged(false); check(t.last==10,"API24 restore");
        t.mPaused=true; t.infinityApplyPlayerRotation("pause"); check(t.last==-1,"pause release");
        t.mPaused=false; t.infinityApplyPlayerRotation("resume"); check(t.last==10,"resume restore");
        t.queryFailed=true; Build.VERSION.SDK_INT=34;
        t.infinityApplyPlayerRotation("query failure"); check(t.last==-1,"fail closed query");
        t.queryFailed=false; t.reject=true;
        t.infinityApplyPlayerRotation("rejection"); check(t.last==-1,"rejected unlock remains released");
        t.reject=false; t.infinityApplyPlayerRotation("retry"); check(t.last==10,"rejected request is retryable");
        System.out.println("PASS: 256 policy states; PiP, multi-window, API24, pause/resume, deduplication and rejection transitions");
      }
    }
    '''
    path = out / 'RotationLifecycleTest.java'
    path.write_text(java)
    subprocess.run(['javac', '-d', str(out), str(config), str(path)], check=True)
    subprocess.run(['java', '-cp', str(out), 'RotationLifecycleTest'], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.out)
