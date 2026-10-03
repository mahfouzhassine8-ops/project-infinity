#!/usr/bin/env python3
"""Strict Java forward delta, plus user-approved two power-button route exception."""
from pathlib import Path
import hashlib, shutil
HERE=Path(__file__).resolve().parent
JAVA=Path('tools/android/packaging/xbmc/src')
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ADDED=('InfinityExitCompletion','InfinityPowerControlActivity','InfinityPowerMenuRoutes')
def once(s,old,new):
    assert s.count(old)==1,(old[:100],s.count(old))
    return s.replace(old,new,1)
def apply_source(src):
    before={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    main=src/JAVA/'Main.java.in';s=main.read_text()
    s=once(s,'  private boolean mInfinityLaunchReady;', '''  private boolean mInfinityLaunchReady;
  final InfinityExitCompletion.Plan mInfinityExitPlan = new InfinityExitCompletion.Plan();
  boolean mInfinityStopped = true;
  private InfinityChooserWeather mInfinityWeatherCapture;
  void infinityStopWeatherCapture() {
    if (mInfinityWeatherCapture != null) mInfinityWeatherCapture.stop();
    mInfinityWeatherCapture = null;
  }
  static boolean infinityClosePending() {
    Main owner = MainActivity;
    return owner != null && !owner.isDestroyed() && owner.mInfinityExitPlan.pending();
  }''')
    s=once(s,'owner != null && owner.mInfinityLaunchReady,','owner != null && owner.mInfinityLaunchReady && !owner.mInfinityExitPlan.pending(),')
    s=once(s,'''  public void onStart()
  {
    super.onStart();''','''  public void onStart()
  {
    mInfinityStopped = false;
    super.onStart();''')
    s=once(s,'    InfinityResumeHubInstaller.apply(this);', '''    InfinityResumeHubInstaller.apply(this);
    InfinityPowerMenuRoutes.applyAsync(this);
    if (!mInfinityExitPlan.pending()) {
      infinityStopWeatherCapture();
      mInfinityWeatherCapture = new InfinityChooserWeather(this, null);
      mInfinityWeatherCapture.start();
    }''')
    s=once(s,'    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onPause");', '''    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onPause");
    infinityStopWeatherCapture();
    if (mInfinityExitPlan.pending()) InfinityExitCompletion.record(this, "exit.normal.beforeAndroidPause");''')
    s=once(s,'    infinityApplyPlayerRotation("pause");','''    infinityApplyPlayerRotation("pause");
    if (mInfinityExitPlan.pending()) InfinityExitCompletion.record(this, "exit.normal.afterAndroidPause");''')
    s=once(s,'    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onStop");','''    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onStop");
    if (mInfinityExitPlan.pending()) InfinityExitCompletion.record(this, "exit.normal.beforeAndroidStop");''')
    s=once(s,'    super.onStop();','''    super.onStop();
    mInfinityStopped = true;
    InfinityExitCompletion.afterStop(this);''')
    s=once(s,'    mInfinityLaunchReady = false;','''    mInfinityLaunchReady = false;
    infinityStopWeatherCapture();
    mInfinityExitPlan.destroying();
    InfinityExitCompletion.record(this, "exit.beforeNativeDestroy");''')
    s=once(s,'      if (MainActivity == this) MainActivity = null;','''      if (MainActivity == this) MainActivity = null;
      mInfinityExitPlan.completed();
      InfinityExitCompletion.record(this, "exit.afterNativeDestroy");''')
    main.write_text(s)

    weather=src/JAVA/'InfinityChooserWeather.java.in';s=weather.read_text()
    s=once(s,'    Main owner=Main.MainActivity;', '    Main owner=Main.infinityLiveActivity();')
    s=once(s,'        accept(result);renderCached();main.postDelayed(refresh,60000);',
        '        boolean accepted=accept(result);renderCached();main.postDelayed(refresh,accepted?60000:10000);')
    s=once(s,'  void renderCached(){','  void renderCached(){\n    if(label==null)return; // Main-owned read-only capture has no chooser View.')
    s=once(s,'    boolean current=Main.MainActivity!=null&&age<2*60*1000L;',
        '    boolean current=Main.infinityLiveActivity()!=null&&age<2*60*1000L;')
    s=once(s,' * Before Kodi runs, only a timestamped real last-known snapshot can be shown.',
        ' * Main captures valid readings while Kodi is running; cold chooser shows a timestamped\n * last-known reading. It never invents live weather or starts Kodi to fetch it.')
    weather.write_text(s)

    prepare=src/JAVA/'InfinityStartupPreparation.java.in';s=prepare.read_text()
    s=once(s,'    long abnormal=0;', '''    trace.event("powerRoutes.begin");
    InfinityPowerMenuRoutes.apply(app);
    trace.event("powerRoutes.end");
    long abnormal=0;''');prepare.write_text(s)

    splash=src/JAVA/'Splash.java.in';s=splash.read_text()
    s=once(s,'    return infinityHealthBuildInfo()+"\\n"+InfinityStartupTrace.report(this)+"\\n"+trace+',
        '    return infinityHealthBuildInfo()+"\\n"+InfinityStartupTrace.report(this)+"\\n"+InfinityExitCompletion.report(this)+"\\n"+trace+')
    s=once(s,'''  protected void startXBMC()
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;''','''  protected void startXBMC()
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
    if (Main.infinityClosePending()) {
      mInfinityStartupTrace.event("handoff.waitClosingOwner");
      showInfinityExperienceChooser(); return;
    }''')
    s=once(s,'''  private void launchInfinityExperience(String experience,boolean explicit,boolean safe)
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;''','''  private void launchInfinityExperience(String experience,boolean explicit,boolean safe)
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
    if (Main.infinityClosePending()) {
      mInfinityStartupTrace.event("handoff.waitClosingOwner");
      showInfinityExperienceChooser();
      android.widget.Toast.makeText(this,"Infinity is finishing its normal close. Saved data is not being reset.",android.widget.Toast.LENGTH_LONG).show();
      return;
    }''')
    s=once(s,'      // Revalidate at dispatch: an Exit can finish the former owner after enqueue.', '''      // Revalidate at dispatch: an Exit can finish the former owner after enqueue.
      if (Main.infinityClosePending()) {
        mInfinityStartupTrace.event("handoff.waitClosingOwner");
        mInfinityLaunchQueued = false;
        mInfinityHandoff.close();
        mInfinityHandoff = new InfinityStartupHandoff(this,findViewById(android.R.id.content));
        if (mInfinityResumed) mInfinityHandoff.resume();
        showInfinityExperienceChooser(); return;
      }''')
    s=once(s,'''  @Override protected void onPause() {
    mInfinityResumed=false;''','''  @Override public void onWindowFocusChanged(boolean hasFocus) {
    super.onWindowFocusChanged(hasFocus);
    if (mInfinityStartupTrace != null) {
      mInfinityStartupTrace.event(hasFocus ? (mInfinityChooserVisible ? "chooser.windowFocused" : "splash.windowFocused") : "splash.windowUnfocused");
      if (hasFocus && mInfinityChooserVisible) {
        final android.view.View visible = findViewById(android.R.id.content);
        visible.postOnAnimation(() -> {
          if (!isFinishing() && !isDestroyed() && hasWindowFocus() && visible.isShown()) mInfinityStartupTrace.event("chooser.focusedFrame");
        });
      }
    }
  }
  @Override protected void onPause() {
    mInfinityResumed=false;''');splash.write_text(s)

    for name in ADDED:shutil.copy2(HERE/(name+'.java.in'),src/JAVA/(name+'.java.in'))
    install=src/'cmake/scripts/android/Install.cmake';s=install.read_text()
    s=once(s,'                  src/InfinityStartupPreparation.java',
        ''.join('                  src/'+n+'.java\n' for n in ADDED)+'                  src/InfinityStartupPreparation.java');install.write_text(s)
    manifest=src/'tools/android/packaging/xbmc/AndroidManifest.xml.in';s=manifest.read_text()
    s=once(s,'        <service android:name=".InfinityExtendedBackgroundService"', '''        <activity android:name=".InfinityPowerControlActivity"
            android:exported="false" android:excludeFromRecents="true"
            android:noHistory="true" android:theme="@android:style/Theme.NoDisplay" />
        <service android:name=".InfinityExtendedBackgroundService"''');manifest.write_text(s)
    gradle=src/'tools/android/packaging/xbmc/build.gradle.in';s=gradle.read_text()
    s=once(once(s,'versionCode 2103298','versionCode 2103299'),'1.0.9-Startup-Reliability-RC1','1.0.9-Graceful-Exit-Handoff-RC1');gradle.write_text(s)
    after={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    expected=sorted([str(JAVA/(n+'.java.in')) for n in ('Main','Splash','InfinityChooserWeather','InfinityStartupPreparation')]+
        ['cmake/scripts/android/Install.cmake','tools/android/packaging/xbmc/build.gradle.in','tools/android/packaging/xbmc/AndroidManifest.xml.in'])
    assert sorted(p for p in before if before[p]!=after[p])==expected
    assert sorted(set(after)-set(before))==sorted(str(JAVA/(n+'.java.in')) for n in ADDED)
    assert not set(before)-set(after)
    assert (src/JAVA/'Main.java.in').read_text().count('InfinityResumeHubInstaller.apply(this);')==1
    return before,after
