#!/usr/bin/env python3
"""Exact 2103297 -> 2103298 Java-only forward repair. No native/resource/skin edits."""
from pathlib import Path
import hashlib, shutil

HERE=Path(__file__).resolve().parent
JAVA=Path('tools/android/packaging/xbmc/src')
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,old,new):
    assert s.count(old)==1,(old[:90],s.count(old))
    return s.replace(old,new,1)

def splash(s):
    s=once(s,'  private boolean mInfinityLaunchQueued;','''  private boolean mInfinityLaunchQueued;
  private InfinityStartupHandoff mInfinityBootstrap, mInfinityChooserFrame;
  private InfinityStartupPreparation.Ticket mInfinityPreparation;
  private InfinityStartupTrace mInfinityStartupTrace;
  private Intent mInfinityPendingMain;
  private boolean mInfinityPreparationReady, mInfinityChooserVisible, mInfinityResumed;
  private long mInfinityAbnormalExit;''')
    begin=s.index('  private class FillCache\n')
    end=s.index('  public void showErrorDialog',begin)
    s=s[:begin]+s[end:]
    begin=s.index('  private void SetupEnvironment()')
    end=s.index('  private boolean CheckPermissions()',begin)
    s=s[:begin]+s[end:]
    begin=s.index('        case StorageChecked:')
    end=s.index('        case StartingXBMC:',begin)
    s=s[:begin]+'''        case StorageChecked:
          mExternalStorageChecked = true;
          mSplash.stopWatchingExternalStorage();
          mSplash.infinityBeginPreparation();
          break;
'''+s[end:]
    s=once(s,'            new FillCache(mSplash).execute();','            mSplash.infinityBeginPreparation();')
    # Cached exit history is read by the worker, never by onCreate/first-frame dispatch.
    s=once(s,'    long timestamp=infinityNewestAbnormalExit();','    long timestamp=mInfinityAbnormalExit;')
    s=once(s,'    out.append("Process uptime: ")','    out.append("Device elapsed uptime: ")')
    s=once(s,'    return infinityHealthBuildInfo()+"\\n"+trace+',
        '    return infinityHealthBuildInfo()+"\\n"+InfinityStartupTrace.report(this)+"\\n"+trace+')
    s=once(s,'''    final Intent request = intent;
    mInfinityLaunchQueued = mInfinityHandoff.enqueue(() -> {''','''    infinityQueueMainRequest(intent);
  }

  private void infinityQueueMainRequest(Intent request) {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
    if (Main.infinityLiveActivity() == null && !mInfinityPreparationReady) {
      mInfinityPendingMain = new Intent(request);
      mInfinityStartupTrace.event("main.waitPreparation");
      android.widget.Toast.makeText(this,"Preparing Infinity; your selection is saved.",android.widget.Toast.LENGTH_SHORT).show();
      return;
    }
    mInfinityPendingMain = null;
    mInfinityLaunchQueued = mInfinityHandoff.enqueue(() -> {''')
    s=once(s,'      Log.i(TAG,"Infinity launch handoff: " + (live ? "live Main" : "fresh Main"));',
        '      mInfinityStartupTrace.event(live ? "handoff.liveMain" : "handoff.freshMain");\n      Log.i(TAG,"Infinity launch handoff: " + (live ? "live Main" : "fresh Main"));')
    # The approved chooser rendering/body is untouched. Only attach evidence for its first draw.
    anchor='  private void showInfinityExperienceChooser()\n  { '
    if anchor not in s:anchor='  private void showInfinityExperienceChooser()\n  {\n'
    assert anchor in s
    s=once(s,anchor,anchor+'''    mInfinityChooserVisible = true;
    if (mInfinityStartupTrace != null) {
      mInfinityStartupTrace.event("chooser.compose");
      if (mInfinityChooserFrame != null) mInfinityChooserFrame.close();
      mInfinityChooserFrame = new InfinityStartupHandoff(this,findViewById(android.R.id.content));
      mInfinityChooserFrame.enqueue(() -> mInfinityStartupTrace.event("chooser.firstFrame"));
      if (mInfinityResumed) mInfinityChooserFrame.resume();
    }
''')
    s=once(s,'''    showInfinityExperienceChooser();
  }

  private int chooserDp''','''    if (!mInfinityChooserVisible) showInfinityExperienceChooser();
  }

  private int chooserDp''')
    begin=s.index('    // Be sure properties are initialized for native',s.index('  public void onCreate(Bundle savedInstanceState)'))
    end=s.index('  @Override protected void onResume()',begin)
    s=s[:begin]+'''    mInfinityStartupTrace = new InfinityStartupTrace(this);
    mInfinityBootstrap = new InfinityStartupHandoff(this,startup);
    mInfinityBootstrap.enqueue(() -> {
      mInfinityStartupTrace.event("splash.firstFrame");
      infinityInitializeStartup();
    });
  }

  private void infinityInitializeStartup() {
    if (isFinishing() || isDestroyed()) return;
    // A genuine live Main bypasses properties/cache work completely.
    if (Main.infinityLiveActivity() != null) { startXBMC(); return; }
    mExternalStorageChecked = Environment.MEDIA_MOUNTED.equals(Environment.getExternalStorageState());
    mPermissionOK = CheckPermissions();
    if (!mPermissionOK) {
      mInfinityStartupTrace.event("permissions.required");
      mStateMachine.sendEmptyMessage(CheckingPermissionsInfo);
    } else if (!mExternalStorageChecked) {
      mInfinityStartupTrace.event("storage.wait");
      startWatchingExternalStorage();
      mStateMachine.sendEmptyMessage(WaitingStorageChecked);
    } else infinityBeginPreparation();
  }

  private void infinityBeginPreparation() {
    if (isFinishing() || isDestroyed() || mInfinityPreparation != null || mInfinityPreparationReady) return;
    // Chooser is Kodi-independent; don't keep Android's logo visible during cache/property I/O.
    Intent incoming=getIntent();
    String preferred=getSharedPreferences(INFINITY_EXPERIENCE_PREFS,MODE_PRIVATE).getString(INFINITY_EXPERIENCE_DEFAULT, "");
    if ((incoming==null || incoming.getAction()==null || Intent.ACTION_MAIN.equals(incoming.getAction())) &&
        !"infinity".equals(preferred) && !"live".equals(preferred) && !mInfinityChooserVisible)
      showInfinityExperienceChooser();
    mInfinityStartupTrace.event("prepare.subscribe");
    mInfinityPreparation=InfinityStartupPreparation.shared().subscribe(this,mInfinityStartupTrace,result -> {
      if (isFinishing() || isDestroyed()) return;
      if (result.error != null) {
        mInfinityPendingMain=null;mErrorMsg=result.error;mStateMachine.sendEmptyMessage(InError);return;
      }
      fXbmcHome=result.home;fPackagePath=result.apk;
      sXbmcHome=result.home.getAbsolutePath();sPackagePath=result.apk.getAbsolutePath();
      mInfinityAbnormalExit=result.abnormalExit;
      mCachingDone=true;mInfinityPreparationReady=true;
      mInfinityStartupTrace.event("prepare.delivered");
      if (mInfinityPendingMain != null) infinityQueueMainRequest(mInfinityPendingMain);
      else startXBMC();
    });
  }

'''+s[end:]
    s=once(s,'    super.onResume();\n    if (mInfinityHandoff != null)',
        '    super.onResume();\n    mInfinityResumed=true;\n    if (mInfinityBootstrap != null) mInfinityBootstrap.resume();\n    if (mInfinityChooserFrame != null) mInfinityChooserFrame.resume();\n    if (mInfinityStartupTrace != null) mInfinityStartupTrace.event("splash.resume");\n    if (mInfinityHandoff != null)')
    s=once(s,'  @Override protected void onPause() {\n    if (mInfinityHandoff != null)',
        '  @Override protected void onPause() {\n    mInfinityResumed=false;\n    if (mInfinityBootstrap != null) mInfinityBootstrap.pause();\n    if (mInfinityChooserFrame != null) mInfinityChooserFrame.pause();\n    if (mInfinityStartupTrace != null) mInfinityStartupTrace.event("splash.pause");\n    if (mInfinityHandoff != null)')
    s=once(s,'  @Override protected void onDestroy() {\n    if (mInfinityHandoff != null)',
        '  @Override protected void onDestroy() {\n    if (mInfinityBootstrap != null) mInfinityBootstrap.close();\n    if (mInfinityChooserFrame != null) mInfinityChooserFrame.close();\n    if (mInfinityPreparation != null) mInfinityPreparation.close();\n    mInfinityPendingMain=null;\n    if (mInfinityStartupTrace != null) mInfinityStartupTrace.event("splash.destroy");\n    if (mInfinityHandoff != null)')
    s=once(s,'  void startWatchingExternalStorage()\n  {','  void startWatchingExternalStorage()\n  {\n    if (mExternalStorageReceiver != null) return;')
    assert 'Thread.sleep' not in s and 'SetupEnvironment' not in s and 'new FillCache' not in s
    return s

def apply_source(src):
    before={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    p=src/JAVA/'Splash.java.in';p.write_text(splash(p.read_text()))
    p=src/JAVA/'Main.java.in';s=p.read_text()
    for old,new in [
      ('    System.loadLibrary("@APP_NAME_LC@");','    InfinityStartupTrace.mainEvent("main.beforeNative");\n    System.loadLibrary("@APP_NAME_LC@");\n    InfinityStartupTrace.mainEvent("main.nativeLoaded");'),
      ('    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onCreate.afterSuper");','    InfinityStartupTrace.mainEvent("main.afterSuper");\n    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onCreate.afterSuper");'),
      ('    mInfinityLaunchReady = true;','    mInfinityLaunchReady = true;\n    InfinityStartupTrace.mainEvent("main.javaReady");'),
      ('    mInfinityLaunchReady = false;','    InfinityStartupTrace.mainEvent("main.destroy");\n    mInfinityLaunchReady = false;'),
      ('  protected void onNewIntent(Intent intent)\n  {','  protected void onNewIntent(Intent intent)\n  {\n    InfinityStartupTrace.mainEvent("main.newIntent");')]:s=once(s,old,new)
    p.write_text(s)
    for name in ('InfinityStartupPreparation','InfinityStartupTrace'):shutil.copy2(HERE/(name+'.java.in'),src/JAVA/(name+'.java.in'))
    p=src/'cmake/scripts/android/Install.cmake';p.write_text(once(p.read_text(),'                  src/InfinityStartupHandoff.java','                  src/InfinityStartupPreparation.java\n                  src/InfinityStartupTrace.java\n                  src/InfinityStartupHandoff.java'))
    p=src/'tools/android/packaging/xbmc/build.gradle.in';p.write_text(once(once(p.read_text(),'versionCode 2103297','versionCode 2103298'),'1.0.9-Cosmic-Motion-Lifecycle-RC1','1.0.9-Startup-Reliability-RC1'))
    after={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    expected=sorted([str(JAVA/n) for n in ('Splash.java.in','Main.java.in')]+['cmake/scripts/android/Install.cmake','tools/android/packaging/xbmc/build.gradle.in'])
    assert sorted(p for p in before if before[p]!=after[p])==expected
    assert sorted(set(after)-set(before))==[str(JAVA/'InfinityStartupPreparation.java.in'),str(JAVA/'InfinityStartupTrace.java.in')]
    assert not set(before)-set(after)
    # Motion, chooser layout, native/window-input, Fold, Resume Hub, Cobra and all assets are untouched.
    assert (src/JAVA/'Main.java.in').read_text().count('InfinityResumeHubInstaller.apply(this);')==1
    return before,after
