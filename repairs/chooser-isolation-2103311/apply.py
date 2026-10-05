#!/usr/bin/env python3
import argparse,hashlib,json,re
from pathlib import Path
PREFIX='tools/android/packaging/xbmc/src/'
SOURCE_MAP='c0c30e22376fcebf86ca8412829352f13906f79f7b5fd876fb8d0b73d69e2d24'
CHANGED={PREFIX+n+'.java.in' for n in ['Splash','Main','InfinityExitCompletion','InfinityPowerControlActivity','InfinityGlassChooser']}|{'tools/android/packaging/xbmc/AndroidManifest.xml.in','cmake/scripts/android/Install.cmake'}
ADDED={PREFIX+n+'.java.in' for n in ['InfinityKodiShutdown','InfinityKodiEntryActivity']}
PROCESSES=['.Main','.InfinityBackgroundControlActivity','.InfinityPowerControlActivity','.InfinityExtendedBackgroundService','.XBMCBroadcastReceiver','.content.XBMCMediaContentProvider','.content.XBMCFileContentProvider','.content.XBMCYTDLContentProvider','.XBMCSearchableActivity','.channels.SyncChannelJobService','.channels.SyncProgramsJobService']
def sha(b):return hashlib.sha256(b).hexdigest()
def manifest(p):return {f.relative_to(p).as_posix():sha(f.read_bytes()) for f in p.rglob('*') if f.is_file()}
def once(s,a,b):assert s.count(a)==1,(a[:80],s.count(a));return s.replace(a,b,1)
def transform(name,s):
 if name=='Splash':
  s=once(s,'  private InfinityStartupPreparation.Ticket mInfinityPreparation;','  private InfinityStartupPreparation.Ticket mInfinityPreparation;\n  private InfinityKodiShutdown.Watch mInfinityKodiWatch;\n  private String mInfinityKodiLaunchToken="", mInfinityCloseError="";\n  private boolean mInfinitySawClosing, mInfinityBootstrapped, mInfinityKodiStateReady;')
  s=s.replace('Main.infinityClosePending()', 'InfinityKodiShutdown.pending()').replace('Main.infinityLiveActivity() != null','InfinityKodiShutdown.live()').replace('Main.infinityLiveActivity() == null','!InfinityKodiShutdown.live()')
  start=s.index('  private void showInfinityClosingRecovery(){');end=s.index('\n  private void showCobraRecovery()',start)
  s=s[:start]+'''  private void showInfinityClosingRecovery(){
    InfinityKodiShutdown.Snapshot owner=InfinityKodiShutdown.state();
    if(!owner.stalled())return;
    cobraRecoveryDialog().setTitle("Infinity is still closing")
        .setMessage("Cleanup has not completed. You can keep waiting, or close this stalled instance and reopen Infinity. Closing it now may interrupt unfinished saves.")
        .setPositiveButton("Close stalled instance",(dialog,which)->{
          InfinityKodiShutdown.Snapshot current=InfinityKodiShutdown.state();
          if(current.pid==owner.pid&&current.owner.equals(owner.owner)&&current.stalled())
            startActivity(InfinityKodiShutdown.force(this,current));
        }).setNegativeButton("Keep waiting",null).show();
  }
''' + s[end:]
  s=once(s,'    Intent incoming = getIntent();','    if(mInfinitySawClosing){showInfinityExperienceChooser();return;}\n    Intent incoming = getIntent();')
  s=once(s,'      Intent target = InfinityStartupHandoff.mainIntent(this,request,live);','      Intent target = new Intent(request);\n      target.setClass(this,InfinityKodiEntryActivity.class);\n      target.setFlags((request.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION)) | Intent.FLAG_ACTIVITY_NEW_TASK);\n      mInfinityKodiLaunchToken=java.util.UUID.randomUUID().toString();\n      target.putExtra(InfinityKodiShutdown.TOKEN,mInfinityKodiLaunchToken);')
  s=once(s,'      startActivity(target);\n      finish();','      startActivity(target);\n      // Keep chooser ownership until the Kodi process acknowledges a live Main.')
  s=once(s,'      mInfinityStartupTrace.event("splash.firstFrame");','      mInfinityBootstrapped=true;\n      mInfinityStartupTrace.event("splash.firstFrame");')
  s=once(s,'    mInfinityStartupTrace = new InfinityStartupTrace(this);','''    mInfinityStartupTrace = new InfinityStartupTrace(this);
    mInfinityKodiWatch=new InfinityKodiShutdown.Watch(this,status->{
      if(isFinishing()||isDestroyed())return;
      mInfinityKodiStateReady=true;
      if(status.pending())mInfinitySawClosing=true;
      if(mInfinityLaunchQueued && status.launch.equals(mInfinityKodiLaunchToken) && status.live && status.alive && !status.pending()){
        finish();return;
      }
      if(mInfinityLaunchQueued && (status.pending() || (!status.error.isEmpty()&&status.launch.equals(mInfinityKodiLaunchToken)))){
        mInfinityLaunchQueued=false;mInfinityKodiLaunchToken="";
        mInfinityHandoff.close();mInfinityHandoff=new InfinityStartupHandoff(this,findViewById(android.R.id.content));
        if(mInfinityResumed)mInfinityHandoff.resume();showInfinityExperienceChooser();
      }
      if(!status.error.isEmpty()&&!status.error.equals(mInfinityCloseError)){
        mInfinityCloseError=status.error;
        android.widget.Toast.makeText(this,status.error,android.widget.Toast.LENGTH_LONG).show();
      }
      if(mInfinityBootstrapped && mInfinityResumed && mInfinityPreparation==null && !mInfinityPreparationReady)infinityInitializeStartup();
    });''')
  s=once(s,'    // A genuine live Main bypasses properties/cache work completely.','''    if(!mInfinityKodiStateReady)return;
    if(InfinityKodiShutdown.pending()){mInfinitySawClosing=true;showInfinityExperienceChooser();return;}
    // A genuine live Main bypasses properties/cache work completely.''')
  s=once(s,'    if (mInfinityPreparation != null) mInfinityPreparation.close();','    if (mInfinityKodiWatch != null) mInfinityKodiWatch.close();\n    if (mInfinityPreparation != null) mInfinityPreparation.close();')
 elif name=='Main':
  s=once(s,'    InfinityStartupTrace.mainEvent("main.beforeNative");','    XBMCProperties.getStringProperty("xbmc.proploaded", "");\n    InfinityKodiShutdown.boot(this,getIntent().getStringExtra(InfinityKodiShutdown.TOKEN));\n    InfinityStartupTrace.mainEvent("main.beforeNative");')
  s=once(s,'    InfinityStartupTrace.mainEvent("main.javaReady");','    InfinityStartupTrace.mainEvent("main.javaReady");\n    InfinityKodiShutdown.publish(this,getIntent().getStringExtra(InfinityKodiShutdown.TOKEN));')
  s=once(s,'    super.onNewIntent(intent);','    super.onNewIntent(intent);\n    InfinityKodiShutdown.publish(this,intent.getStringExtra(InfinityKodiShutdown.TOKEN));')
 elif name=='InfinityExitCompletion':
  s=once(s,'    final Context app = context.getApplicationContext(); RECORDS.execute(() -> write(app, phase));','    InfinityKodiShutdown.publish(context,null);\n    final Context app = context.getApplicationContext(); RECORDS.execute(() -> write(app, phase));')
  s=once(s,'    prefs.edit().putString("history", next.toString()).commit();','''    prefs.edit().putString("history", next.toString()).commit();
    android.util.AtomicFile file=new android.util.AtomicFile(new java.io.File(app.getFilesDir(),"infinity-close-history.txt"));
    java.io.FileOutputStream output=null;
    try{output=file.startWrite();output.write(next.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));file.finishWrite(output);}
    catch(java.io.IOException failure){if(output!=null)file.failWrite(output);}''')
  s=once(s,'    return "Explicit close / force-close evidence','''    try{
      byte[] bytes=new android.util.AtomicFile(new java.io.File(context.getFilesDir(),"infinity-close-history.txt")).readFully();
      if(bytes.length<65536)history=new String(bytes,java.nio.charset.StandardCharsets.UTF_8);
    }catch(java.io.IOException unavailable){}
    return "Explicit close / force-close evidence''')
 elif name=='InfinityPowerControlActivity':
  s=once(s,'        InfinityExitCompletion.requestForce(owner, this);','        if(InfinityKodiShutdown.expected(getIntent()) && (!getIntent().hasExtra(InfinityKodiShutdown.OWNER) ||\n            (owner!=null && owner.mInfinityExitPlan.stalled(android.os.SystemClock.elapsedRealtime()))))\n          InfinityExitCompletion.requestForce(owner, this);')
 elif name=='InfinityGlassChooser':
  s=once(s,'private boolean closePending,closeReady,progressPosted;','private boolean closePending,closeReady,closeFailed,progressPosted;')
  s=once(s,'InfinityExitCompletion.Plan.Phase phase=InfinityExitCompletion.closePhase();','InfinityExitCompletion.Plan.Phase phase=InfinityKodiShutdown.phase();\n      boolean failed=!InfinityKodiShutdown.state().alive && InfinityKodiShutdown.state().closeAt>0 && !InfinityKodiShutdown.state().complete;')
  s=once(s,'boolean pending=phase!=InfinityExitCompletion.Plan.Phase.RUNNING && phase!=InfinityExitCompletion.Plan.Phase.COMPLETE;','boolean pending=InfinityKodiShutdown.pending();')
  s=once(s,'if(phase!=shownClosePhase){','if(phase!=shownClosePhase || failed!=closeFailed){\n        closeFailed=failed;')
  s=once(s,'setContentDescription(pending ?','setContentDescription(failed ? "Kodi ended without confirmed cleanup. Open Health Center" : pending ?')
  s=once(s,'if(!cobra && (closePending || closeReady)){','if(!cobra && (closePending || closeReady || closeFailed)){')
  s=s.replace('p.setColor(light?0xff079de8:0xff39caff);','p.setColor(closeFailed?0xffffac45:(light?0xff079de8:0xff39caff));')
  s=once(s,'if(!wasPending){displayed=0;closeTargetSweep=0;}','if(!wasPending && !failed){displayed=0;closeTargetSweep=0;}')
 else:raise AssertionError(name)
 return s

def apply(source,out):
 before=manifest(source);assert len(before)==250 and sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==SOURCE_MAP,'Wrong complete 3310 parent'
 for name in ['Splash','Main','InfinityExitCompletion','InfinityPowerControlActivity','InfinityGlassChooser']:
  p=source/(PREFIX+name+'.java.in');p.write_text(transform(name,p.read_text()))
 for name in ['InfinityKodiShutdown','InfinityKodiEntryActivity']:
  (source/(PREFIX+name+'.java.in')).write_text((Path(__file__).parent/(name+'.java.in')).read_text())
 p=source/'cmake/scripts/android/Install.cmake';p.write_text(once(p.read_text(),'                  src/InfinityStartupPreparation.java','                  src/InfinityKodiShutdown.java\n                  src/InfinityKodiEntryActivity.java\n                  src/InfinityStartupPreparation.java'))
 p=source/'tools/android/packaging/xbmc/AndroidManifest.xml.in';s=p.read_text()
 for name in PROCESSES:
  s=once(s,'android:name="'+name+'"','android:name="'+name+'" android:process=":kodi"')
 s=once(s,'        <!-- Infinity Live is a second, isolated Android environment inside','        <activity android:name=".InfinityKodiEntryActivity" android:process=":kodi"\n            android:exported="false" android:launchMode="singleTask" android:excludeFromRecents="true"\n            android:theme="@style/AppTheme" />\n\n        <!-- Infinity Live is a second, isolated Android environment inside')
 p.write_text(s)
 after=manifest(source);assert set(after)-set(before)==ADDED and {n for n in before if before[n]!=after[n]}==CHANGED
 out.mkdir(parents=True,exist_ok=True)
 (out/'SOURCE-PRESERVATION.json').write_text(json.dumps({'apk_parent':2103310,'before':before,'after':after,'changed':sorted(CHANGED),'added':sorted(ADDED),'unchanged_files':243,'cobra_source_changed':False,'skin_changed':False,'native_changed':False},indent=2)+'\n')
 print('PASS: exact 3310 parent; only chooser isolation, Kodi routing/status and declared registration changed. Cobra, native and skin source retained.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();apply(a.source,a.out)
