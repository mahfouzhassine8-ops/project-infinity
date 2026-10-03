#!/usr/bin/env python3
"""Strict forward Java delta over the reproduced 3296 composition. Never touches native/assets."""
from pathlib import Path
import hashlib, json, shutil

HERE=Path(__file__).resolve().parent
JAVA=Path('tools/android/packaging/xbmc/src')
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def once(s,old,new):
    assert s.count(old)==1, (old[:100],s.count(old))
    return s.replace(old,new,1)

def motion(s):
    s=once(s,'stage=new Stage(context,light,actions);','stage=new Stage(context,light,actions);backdrop.protectedStage=stage;')
    s=once(s,'final boolean light;Bitmap plate;boolean framePending,attached,focused=true,motionDisabled,reducedMotion;',
        'final boolean light;Bitmap plate;Stage protectedStage;\n    final android.graphics.Rect protectedRect=new android.graphics.Rect();\n    boolean framePending,attached,focused=true,motionDisabled,reducedMotion;')
    s=once(s,'&&isShown()&&isHardwareAccelerated();','&&isShown();')
    s=once(s,'framePending=true;postDelayed(frame,33);','framePending=postDelayed(frame,33);')
    s=once(s,'      float seconds=phaseMillis/1000f,cx=w*.5f,cy=h*.42f;', '''      int save=c.save();
      // Explicitly exclude all control bounds, including glass and spaces within cards.
      // Coordinates belong to the current chooser window; scrolling/resizing is respected.
      if(protectedStage!=null && getParent() instanceof ViewGroup){
        ViewGroup root=(ViewGroup)getParent();
        for(int i=0;i<protectedStage.getChildCount();i++){
          View control=protectedStage.getChildAt(i);
          if(control.getVisibility()!=VISIBLE)continue;
          control.getDrawingRect(protectedRect);root.offsetDescendantRectToMyCoords(control,protectedRect);
          protectedRect.offset(-getLeft(),-getTop());
          c.clipRect(protectedRect,android.graphics.Region.Op.DIFFERENCE);
        }
      }
      float density=getResources().getDisplayMetrics().density;
      float seconds=phaseMillis/1000f,cx=w*.5f,cy=h*.42f;''')
    s=once(s,'seconds*(.009f+depth*.012f)','seconds*(.028f+depth*.045f)')
    s=once(s,'(light?55:95)','(light?170:215)')
    s=once(s,'p.setStrokeWidth(.6f+depth*.75f);','p.setStrokeWidth((.7f+depth*.8f)*density);')
    s=once(s,'float streak=(1.5f+burst*16)*depth;','float streak=(2.2f+burst*24)*depth*density;')
    s=once(s,'        c.drawLine(x,y,x+(float)Math.cos(a)*streak,y+(float)Math.sin(a)*streak,p);\n      }',
        '        c.drawLine(x,y,x+(float)Math.cos(a)*streak,y+(float)Math.sin(a)*streak,p);\n      }\n      c.restoreToCount(save);')
    return s

def main(s):
    s=once(s,'  public static Main MainActivity = null;', '''  public static Main MainActivity = null;
  private boolean mInfinityLaunchReady;
  static Main infinityLiveActivity() {
    Main owner = MainActivity;
    return InfinityStartupHandoff.isLive(owner, owner != null && owner.mInfinityLaunchReady,
        owner != null && owner.mInfinityDestroyed) ? owner : null;
  }''')
    s=once(s,'  @Override\n  protected void onNewIntent(Intent intent)', '  @Override\n  protected void onNewIntent(Intent intent)')
    anchor='''    }
  }

  @Override
  protected void onNewIntent(Intent intent)'''
    s=once(s,anchor,'''    }
    mInfinityLaunchReady = true;
  }

  @Override
  protected void onNewIntent(Intent intent)''')
    s=once(s,'    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onDestroy");',
        '    mInfinityLaunchReady = false;\n    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onDestroy");')
    return s

def splash(s):
    s=once(s,'  private int mState = Uninitialized;', '  private int mState = Uninitialized;\n  private InfinityStartupHandoff mInfinityHandoff;\n  private boolean mInfinityLaunchQueued;')
    s=once(s,'      mSplash.mState = msg.what;', '      if (mSplash.isFinishing() || mSplash.isDestroyed()) return;\n      mSplash.mState = msg.what;')
    s=once(s,'''    if (mExternalStorageReceiver != null)
      unregisterReceiver(mExternalStorageReceiver);''', '''    if (mExternalStorageReceiver != null) {
      unregisterReceiver(mExternalStorageReceiver);
      mExternalStorageReceiver = null;
    }''')
    s=once(s,'''  protected void startXBMC()
  {
    Intent incoming''', '''  protected void startXBMC()
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
    if (Main.infinityLiveActivity() != null) {
      launchInfinityExperience("infinity",false,false);
      return;
    }
    Intent incoming''')
    s=once(s,'''  private void launchInfinityExperience(String experience,boolean explicit,boolean safe)
  {
    Intent intent''', '''  private void launchInfinityExperience(String experience,boolean explicit,boolean safe)
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
    Intent intent''')
    s=once(s,'''    intent.addFlags(Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP);
    startActivity(intent);
    finish();''', '''    if ("live".equals(experience)) {
      // Preserve Cobra's original routing and flags exactly.
      intent.addFlags(Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP);
      startActivity(intent);
      finish();
      return;
    }
    final Intent request = intent;
    mInfinityLaunchQueued = mInfinityHandoff.enqueue(() -> {
      // Revalidate at dispatch: an Exit can finish the former owner after enqueue.
      boolean live = Main.infinityLiveActivity() != null;
      Intent target = InfinityStartupHandoff.mainIntent(this,request,live);
      Log.i(TAG,"Infinity launch handoff: " + (live ? "live Main" : "fresh Main"));
      startActivity(target);
      finish();
    });''')
    start=s.index('    // Check if @APP_NAME@ is not already running')
    end=s.index('    mStateMachine.sendEmptyMessage(Checking);',start)
    s=s[:start]+'''    // A task entry is not proof of a living NativeActivity. Only reuse a fully
    // initialized owner that has not begun finishing/destroying.
    if (Main.infinityLiveActivity() != null) {
      startXBMC();
      return;
    }

'''+s[end:]
    s=once(s,'''    super.onCreate(savedInstanceState);

    // Be sure''', '''    super.onCreate(savedInstanceState);
    // Every early-return route owns real non-black content before it can hand off.
    setContentView(R.layout.activity_splash);
    mProgress = (ProgressBar) findViewById(R.id.progressBar1);
    mTextView = (TextView) findViewById(R.id.textView1);
    View startup = findViewById(android.R.id.content);
    int startupColor = "light".equals(chooserAppearanceMode()) ? 0xffeaf3fc : 0xff10233a;
    if (startup instanceof android.view.ViewGroup && ((android.view.ViewGroup)startup).getChildCount() > 0)
      ((android.view.ViewGroup)startup).getChildAt(0).setBackgroundColor(startupColor);
    getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(startupColor));
    mTextView.setText("Starting Infinity...");
    mTextView.setTextColor("light".equals(chooserAppearanceMode()) ? 0xff071a30 : 0xfff5f7fc);
    mInfinityHandoff = new InfinityStartupHandoff(this,startup);

    // Be sure''')
    s=once(s,'''    setContentView(R.layout.activity_splash);
    mProgress = (ProgressBar) findViewById(R.id.progressBar1);
    mTextView = (TextView) findViewById(R.id.textView1);

    if (mState == InError''', '''    if (mState == InError''')
    anchor='  private boolean isAndroidTV()'
    s=once(s,anchor,'''  @Override protected void onResume() {
    super.onResume();
    if (mInfinityHandoff != null) mInfinityHandoff.resume();
  }

  @Override protected void onPause() {
    if (mInfinityHandoff != null) mInfinityHandoff.pause();
    super.onPause();
  }

  @Override protected void onNewIntent(Intent intent) {
    super.onNewIntent(intent);
    setIntent(intent);
    if (!mInfinityLaunchQueued && mCachingDone && mExternalStorageChecked && mPermissionOK)
      startXBMC();
  }

  @Override protected void onDestroy() {
    if (mInfinityHandoff != null) mInfinityHandoff.close();
    mStateMachine.removeCallbacksAndMessages(null);
    stopWatchingExternalStorage();
    super.onDestroy();
  }

'''+anchor)
    return s

def apply_source(src):
    before={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    for name,patch in [('InfinityGlassChooser.java.in',motion),('Main.java.in',main),('Splash.java.in',splash)]:
        p=src/JAVA/name;p.write_text(patch(p.read_text()))
    shutil.copy2(HERE/'InfinityStartupHandoff.java.in',src/JAVA/'InfinityStartupHandoff.java.in')
    p=src/'cmake/scripts/android/Install.cmake'
    p.write_text(once(p.read_text(),'                  src/InfinityGlassChooser.java','                  src/InfinityStartupHandoff.java\n                  src/InfinityGlassChooser.java'))
    p=src/'tools/android/packaging/xbmc/build.gradle.in'
    p.write_text(once(once(p.read_text(),'versionCode 2103296','versionCode 2103297'),'1.0.9-Cosmic-Chooser-RC1','1.0.9-Cosmic-Motion-Lifecycle-RC1'))
    after={str(p.relative_to(src)):H(p) for p in src.rglob('*') if p.is_file()}
    changed=sorted(p for p in before if before[p]!=after.get(p))
    expected=sorted([str(JAVA/n) for n in ('InfinityGlassChooser.java.in','Main.java.in','Splash.java.in')]+['cmake/scripts/android/Install.cmake','tools/android/packaging/xbmc/build.gradle.in'])
    assert changed==expected,changed
    assert sorted(set(after)-set(before))==[str(JAVA/'InfinityStartupHandoff.java.in')]
    assert not set(before)-set(after)
    # Resume Hub startup hook and every other class/assets/native remain unchanged.
    assert (src/JAVA/'Main.java.in').read_text().count('InfinityResumeHubInstaller.apply(this);')==1
    return before,after
