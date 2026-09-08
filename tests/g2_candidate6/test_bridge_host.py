"""Execute the real adapter against JVM fake Android/native collaborators.

The production bridge is separately compiled against the real SDK. These host
policy tests are NOT an emulator test or evidence of device playback/PiP success.
"""
from pathlib import Path
import shutil, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCES={
'android/os/Build.java':'''package android.os; public final class Build { public static final class VERSION { public static int SDK_INT=34; } }''',
'android/os/Looper.java':'''package android.os; public final class Looper { public static final Looper MAIN=new Looper(); public static Looper current=MAIN; public static Looper myLooper(){return current;} public static Looper getMainLooper(){return MAIN;} }''',
'android/util/Log.java':'''package android.util; public final class Log { public static int w(String t,String m,Throwable e){return 0;} }''',
'android/util/Rational.java':'''package android.util; public final class Rational { public final int num,den; public Rational(int n,int d){num=n;den=d;} }''',
'android/content/pm/PackageManager.java':'''package android.content.pm; public final class PackageManager { public static final String FEATURE_PICTURE_IN_PICTURE="android.software.picture_in_picture"; public boolean supported=true; public boolean hasSystemFeature(String n){return supported;} }''',
'android/app/PictureInPictureParams.java':'''package android.app;
import android.util.Rational;
public final class PictureInPictureParams {
 public Rational aspect; public boolean autoTouched,auto;
 public static final class Builder {
  private final PictureInPictureParams p=new PictureInPictureParams();
  public Builder setAspectRatio(Rational r){p.aspect=r;return this;}
  public Builder setAutoEnterEnabled(boolean b){p.autoTouched=true;p.auto=b;return this;}
  public PictureInPictureParams build(){return p;}
 }
}''',
'com/projectinfinity/kodi/Main.java':'''package com.projectinfinity.kodi;
import android.app.PictureInPictureParams; import android.content.pm.PackageManager;
public final class Main {
 public int version=2,entries,updates,syncs; public boolean video,finishing,destroyed,pip,linkage;
 public RuntimeException rejection; public PackageManager pm=new PackageManager();
 public PictureInPictureParams last;
 private void check(){if(linkage)throw new UnsatisfiedLinkError("fixture");}
 public int _infinityBridgeVersion(){check();return version;}
 public boolean _infinityHasActiveVideo(){check();return video;}
 public void _infinitySyncDisplayState(){check();++syncs;}
 public int _infinitySystemThemeMode(){check();return 2;}
 public int _infinityWindowWidth(){check();return 2208;}
 public int _infinityWindowHeight(){check();return 1840;}
 public boolean isFinishing(){return finishing;} public boolean isDestroyed(){return destroyed;}
 public boolean isInPictureInPictureMode(){return pip;} public PackageManager getPackageManager(){return pm;}
 public void setPictureInPictureParams(PictureInPictureParams p){if(rejection!=null)throw rejection;last=p;++updates;}
 public boolean enterPictureInPictureMode(PictureInPictureParams p){if(rejection!=null)throw rejection;last=p;++entries;return true;}
}''',
'com/projectinfinity/kodi/BridgePolicyTests.java':'''package com.projectinfinity.kodi;
import android.os.Build;import android.os.Looper;
public final class BridgePolicyTests {
 private static int tests;
 private static void pass(String s){System.out.println("PASS: "+s);++tests;}
 private static Main fresh(){Build.VERSION.SDK_INT=34;Looper.current=Looper.MAIN;return new Main();}
 public static void main(String[] args){
  assert !InfinityCoreBridge.enterInfinityPictureInPicture(null);
  InfinityCoreBridge.updateInfinityPictureInPictureParams(null);InfinityCoreBridge.syncDisplayState(null);
  assert InfinityCoreBridge.getNativeWindowWidth(null)==-1;
  assert InfinityCoreBridge.getNativeWindowHeight(null)==-1;
  assert InfinityCoreBridge.getSystemThemeMode(null)==0;
  assert InfinityCoreBridge.getBridgeVersion(null)==0;
  assert !InfinityCoreBridge.hasActiveVideoPlayer(null);pass("null activity fails closed");
  Main m=fresh();m.version=3;m.video=true;
  assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);InfinityCoreBridge.syncDisplayState(m);
  assert m.syncs==0;assert InfinityCoreBridge.getNativeWindowWidth(m)==-1;pass("v3 engine is not treated as G2 v2");
  m=fresh();m.linkage=true;
  assert InfinityCoreBridge.getBridgeVersion(m)==0;assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);
  InfinityCoreBridge.syncDisplayState(m);pass("missing JNI entry does not escape as LinkageError");
  m=fresh();m.video=true;Build.VERSION.SDK_INT=25;
  assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);InfinityCoreBridge.updateInfinityPictureInPictureParams(m);assert m.updates==0;pass("old SDK skips PiP");
  m=fresh();m.video=true;m.pm.supported=false;assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);InfinityCoreBridge.updateInfinityPictureInPictureParams(m);assert m.updates==0;pass("missing platform feature skips PiP");
  m=fresh();m.video=true;m.finishing=true;assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);pass("finishing activity skips PiP");
  m=fresh();m.video=true;m.destroyed=true;assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);pass("destroyed activity skips PiP");
  m=fresh();m.video=true;Looper.current=null;assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);pass("off-main-thread PiP is rejected, not queued");
  m=fresh();m.video=true;m.pip=true;assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);assert m.entries==0;pass("existing PiP is not reentered");
  m=fresh();assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);assert m.entries==0;pass("idle/audio gate preserved");
  m=fresh();m.video=true;assert InfinityCoreBridge.enterInfinityPictureInPicture(m);assert m.entries==1;assert m.last.aspect.num==16 && m.last.aspect.den==9;pass("normal #5 explicit entry policy preserved");
  m=fresh();Build.VERSION.SDK_INT=30;InfinityCoreBridge.updateInfinityPictureInPictureParams(m);assert m.updates==1 && !m.last.autoTouched;pass("API 30 does not invoke API 31 auto-enter method");
  m=fresh();InfinityCoreBridge.updateInfinityPictureInPictureParams(m);assert m.updates==1 && m.last.autoTouched && !m.last.auto;pass("API 31+ still disables auto-entry, just like #5");
  for(RuntimeException e:new RuntimeException[]{new IllegalArgumentException(),new IllegalStateException(),new SecurityException()}){
   m=fresh();m.video=true;m.rejection=e;assert !InfinityCoreBridge.enterInfinityPictureInPicture(m);InfinityCoreBridge.updateInfinityPictureInPictureParams(m);assert m.entries==0 && m.updates==0;pass(e.getClass().getSimpleName()+" is contained");
  }
  m=fresh();m.video=true;assert InfinityCoreBridge.hasActiveVideoPlayer(m);assert InfinityCoreBridge.getBridgeVersion(m)==2;
  assert InfinityCoreBridge.getSystemThemeMode(m)==2;assert InfinityCoreBridge.getNativeWindowWidth(m)==2208;assert InfinityCoreBridge.getNativeWindowHeight(m)==1840;InfinityCoreBridge.syncDisplayState(m);assert m.syncs==1;pass("all six unchanged G2 JNI endpoints forward correctly");
  assert tests==17;System.out.println("17 HOST POLICY CASES PASSED. Android device behavior remains untested.");
 }
}'''
}
with tempfile.TemporaryDirectory(prefix='g2-host-tests-') as tmp:
 root=Path(tmp)
 for name,src in SOURCES.items():
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(src)
 shutil.copyfile(ROOT/'mapping/g2-candidate6/InfinityCoreBridge.java',root/'com/projectinfinity/kodi/InfinityCoreBridge.java')
 out=root/'classes';out.mkdir()
 subprocess.run(['javac','-source','8','-target','8','-d',str(out)]+[str(p) for p in root.rglob('*.java')],check=True)
 subprocess.run(['java','-ea','-cp',str(out),'com.projectinfinity.kodi.BridgePolicyTests'],check=True)
