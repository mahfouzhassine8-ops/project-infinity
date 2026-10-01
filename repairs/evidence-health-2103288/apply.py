#!/usr/bin/env python3
"""Add Evidence-First Health Center Responsive/Fold trace to exact 2103284 Android shell.

Package over signed 2103285 so the accepted native FD repair remains byte-identical.
This pass changes Android diagnostics/UI only. It does not change Kodi native resize behavior,
the installed skin, player, providers, accounts, databases, recovery policy or user data.
"""
from pathlib import Path
import argparse,hashlib,json

VC=2103288
REL='1.0.9-Evidence-First-Health-RC1'
BASE_COMMIT='c0c150b30008cee17df39e2a79a0c07e9a91f72a'
BASE_APK='64ed5ce79096a3e09d02907cf72d3a5c4ad20186da231898c92db83e540d266b'
BASE_ENGINE='f6eb05f091bfe7a624105a0a83744a292e229b385d39c1b6a23f8bf954a2522a'
MAIN=Path('tools/android/packaging/xbmc/src/Main.java.in')
SPLASH=Path('tools/android/packaging/xbmc/src/Splash.java.in')
HEALTH=Path('tools/android/packaging/xbmc/src/InfinityGlassHealth.java.in')
INSTALL=Path('cmake/scripts/android/Install.cmake')
GRADLE=Path('tools/android/packaging/xbmc/build.gradle.in')
TRACE=Path('tools/android/packaging/xbmc/src/InfinityResponsiveTrace.java.in')
PRE={
 MAIN:'6334886ca40d7b634be05b988606a10cdb7cd4e72c5089640b8b0b9ea1affef1',
 SPLASH:'ca7dfe911c2633f4275fb9419c55efbc00de7f1887c3db8315d1eb3cc04f18b0',
 HEALTH:'49cca75cb37251d0fc321f0c613125cd29bae9541204f41f3e2c62051b33c565',
 INSTALL:'232d188d10fcbe35e8b02903856755240f9d14e88b61a44d50b32407be87078a',
 GRADLE:'cbd359f2d98599b24236263e7c26287f7131e7daf83c9c43d681b7c29653992e',
}
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(p.read_bytes())
def once(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'{label}: expected one exact anchor, got {n}')
 return s.replace(a,b,1)

def patch_health(s):
 old='''  void menu(String[][] rows,Runnable[] handlers){
    if(rows==null||handlers==null||rows.length!=4||handlers.length!=4)throw new IllegalArgumentException("Health menu contract");
'''
 new='''  void menu(String[][] rows,Runnable[] handlers){
    if(rows==null||handlers==null||rows.length<1||rows.length>8||rows.length!=handlers.length)
      throw new IllegalArgumentException("Health menu contract");
'''
 return once(s,old,new,'variable health rows')

def trace_methods():
 return r'''
  private long[] infinityResponsiveTraceState()
  {
    try { return _infinityGetState(); }
    catch (RuntimeException | LinkageError ignored) { return null; }
  }

  private void infinityTraceWindow(String event)
  {
    InfinityResponsiveTrace.capture(this, event, mMainView, infinityResponsiveTraceState(),
        mInfinityViewSize, mInfinityManagedSize);
  }

  private void infinityTraceWindowSettled(final String event)
  {
    if (!InfinityResponsiveTrace.isEnabled(this)) return;
    View target = mMainView != null ? mMainView : getWindow().getDecorView();
    if (target != null) target.post(() -> infinityTraceWindow(event));
    else infinityTraceWindow(event);
  }

'''

def patch_main(s):
 s=once(s,'    infinityApplyPlayerRotation("attach");\n',
        '    infinityApplyPlayerRotation("attach");\n    infinityTraceWindowSettled("main.attach");\n','attach trace')
 s=once(s,'    InfinityExtendedBackgroundService.sync(this);\n  }\n\n  @Override\n  public void onPause()',
        '    InfinityExtendedBackgroundService.sync(this);\n    infinityTraceWindowSettled("main.resume");\n  }\n\n  @Override\n  public void onPause()','resume trace')
 s=once(s,'  public void onPause()\n  {\n    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onPause");',
        '  public void onPause()\n  {\n    infinityTraceWindow("main.pause");\n    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onPause");','pause trace')
 s=once(s,'    if (mInfinityRefresh != null) mInfinityRefresh.apply("window");\n  }\n\n  @Override\n  public void onPictureInPictureModeChanged(boolean active, Configuration configuration)',
        '    if (mInfinityRefresh != null) mInfinityRefresh.apply("window");\n    infinityTraceWindow("main.configuration");\n    infinityTraceWindowSettled("main.configuration.settled");\n  }\n\n  @Override\n  public void onPictureInPictureModeChanged(boolean active, Configuration configuration)','configuration trace')
 s=once(s,'    infinityApplyPlayerRotation("picture-in-picture");\n  }\n\n  @Override\n  public void onMultiWindowModeChanged(boolean active, Configuration configuration)',
        '    infinityApplyPlayerRotation("picture-in-picture");\n    infinityTraceWindowSettled("main.pip");\n  }\n\n  @Override\n  public void onMultiWindowModeChanged(boolean active, Configuration configuration)','pip trace')
 s=once(s,'    infinityApplyPlayerRotation("multi-window");\n  }\n\n  @Override\n  public void onWindowFocusChanged(boolean hasFocus)',
        '    infinityApplyPlayerRotation("multi-window");\n    infinityTraceWindowSettled("main.multiwindow");\n  }\n\n  @Override\n  public void onWindowFocusChanged(boolean hasFocus)','multi trace')
 s=once(s,'    if (hasFocus && mInfinityRefresh != null) mInfinityRefresh.apply("focus");\n  }\n\n  @Override\n  public void onStop()',
        '    if (hasFocus && mInfinityRefresh != null) mInfinityRefresh.apply("focus");\n    if (hasFocus) infinityTraceWindowSettled("main.focus");\n  }\n\n  @Override\n  public void onStop()','focus trace')
 s=once(s,'  public void onStop()\n  {\n    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onStop");',
        '  public void onStop()\n  {\n    infinityTraceWindow("main.stop");\n    InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.onStop");','stop trace')
 s=once(s,'    mInfinityWindowMode = mode | (managed ? 4 : 0);\n  }\n\n  public long infinityGetWindowSize()',
        '    mInfinityWindowMode = mode | (managed ? 4 : 0);\n    infinityTraceWindow("bridge.publish");\n  }\n\n'+trace_methods()+'  public long infinityGetWindowSize()','publish trace')
 return s

def patch_splash(s):
 # Binary trace export result is completely separate from the existing text report.
 s=once(s,'  private static final int INFINITY_HEALTH_EXPORT_RESULT_CODE = 8951;\n  private String mInfinityHealthExportText = "";',
        '  private static final int INFINITY_HEALTH_EXPORT_RESULT_CODE = 8951;\n'
        '  private static final int INFINITY_RESPONSIVE_TRACE_EXPORT_RESULT_CODE = 8952;\n'
        '  private String mInfinityHealthExportText = "";\n'
        '  private java.io.File mInfinityResponsiveTraceExportFile = null;','trace result state')
 old='''    if (requestCode == INFINITY_HEALTH_EXPORT_RESULT_CODE)
    {
'''
 new='''    if (requestCode == INFINITY_RESPONSIVE_TRACE_EXPORT_RESULT_CODE)
    {
      if (resultCode == RESULT_OK && data != null && data.getData() != null &&
          mInfinityResponsiveTraceExportFile != null && mInfinityResponsiveTraceExportFile.isFile())
      {
        java.io.InputStream input=null;java.io.OutputStream output=null;
        try
        {
          input=new java.io.FileInputStream(mInfinityResponsiveTraceExportFile);
          output=getContentResolver().openOutputStream(data.getData(),"w");
          if(output==null)throw new java.io.IOException("No document output stream");
          byte[] buffer=new byte[8192];int read;
          while((read=input.read(buffer))>0)output.write(buffer,0,read);
          output.flush();
          android.widget.Toast.makeText(this,"Responsive/Fold evidence ZIP saved.",android.widget.Toast.LENGTH_SHORT).show();
        }
        catch(Exception e)
        {
          android.widget.Toast.makeText(this,"Could not save the Responsive/Fold evidence ZIP.",android.widget.Toast.LENGTH_LONG).show();
        }
        finally
        {
          if(input!=null)try{input.close();}catch(Exception ignored){}
          if(output!=null)try{output.close();}catch(Exception ignored){}
        }
      }
      if(mInfinityResponsiveTraceExportFile!=null)mInfinityResponsiveTraceExportFile.delete();
      mInfinityResponsiveTraceExportFile=null;
      return;
    }
    if (requestCode == INFINITY_HEALTH_EXPORT_RESULT_CODE)
    {
'''
 s=once(s,old,new,'trace onActivityResult')
 oldrows='''    String[][] rows={
      {"↺","Recent crashes & exits","See Android-reported Infinity crashes, ANRs and abnormal exits."},
      {"⇧","Export diagnostic report","Save a shareable Infinity diagnostic text report."},
      {"⧉","Copy diagnostic report","Copy the full report to your clipboard for quick sharing."},
      {"ⓘ","Build & device info","View Infinity version, Android build and device details."}
    };
    Runnable[] actions=new Runnable[]{
      ()->{dialog.dismiss();infinityShowHealthText("Recent crashes & exits",infinityHealthExitHistory(false));},
      ()->{dialog.dismiss();infinityExportHealthReport();},
      ()->{infinityCopyHealthReport();},
      ()->{dialog.dismiss();infinityShowHealthText("Build & device info",infinityHealthBuildInfo());}
    };'''
 newrows='''    final boolean responsiveTracing=InfinityResponsiveTrace.isEnabled(this);
    String[][] rows={
      {"↔",responsiveTracing?"Stop & export Responsive/Fold Trace":"Start Responsive/Fold Trace",
        responsiveTracing?"Stop the evidence capture and save one diagnostic ZIP.":"Record Android window, Kodi bridge geometry and safe skin/profile events while you reproduce the resize problem."},
      {"↺","Recent crashes & exits","See Android-reported Infinity crashes, ANRs and abnormal exits."},
      {"⇧","Export diagnostic report","Save a shareable Infinity diagnostic text report."},
      {"⧉","Copy diagnostic report","Copy the full report to your clipboard for quick sharing."},
      {"ⓘ","Build & device info","View Infinity version, Android build and device details."}
    };
    Runnable[] actions=new Runnable[]{
      ()->{dialog.dismiss();if(responsiveTracing)infinityExportResponsiveTrace();else infinityStartResponsiveTrace();},
      ()->{dialog.dismiss();infinityShowHealthText("Recent crashes & exits",infinityHealthExitHistory(false));},
      ()->{dialog.dismiss();infinityExportHealthReport();},
      ()->{infinityCopyHealthReport();},
      ()->{dialog.dismiss();infinityShowHealthText("Build & device info",infinityHealthBuildInfo());}
    };'''
 if s.count(oldrows)!=2:raise RuntimeError('Expected glass and fallback Health row blocks')
 s=s.replace(oldrows,newrows)
 oldreport='''  private String infinityHealthReport()
  {
    return infinityHealthBuildInfo()+"\\nRecent process exits\\n====================\\n"+
        infinityHealthExitHistory(true);
  }
'''
 newreport='''  private String infinityHealthReport()
  {
    String trace=InfinityResponsiveTrace.isEnabled(this)
        ?"Responsive/Fold trace: ACTIVE — reproduce the problem, then return to Health Center and stop/export it.\\n"
        :"Responsive/Fold trace\\n=====================\\n"+InfinityResponsiveTrace.latestSummary(this)+"\\n";
    return infinityHealthBuildInfo()+"\\n"+trace+"\\nRecent process exits\\n====================\\n"+
        infinityHealthExitHistory(true);
  }

  private void infinityStartResponsiveTrace()
  {
    try
    {
      InfinityResponsiveTrace.start(this);
      android.widget.Toast.makeText(this,
          "Responsive/Fold trace started. Reproduce the resize problem, then return to Health Center.",
          android.widget.Toast.LENGTH_LONG).show();
    }
    catch(Exception e)
    {
      android.widget.Toast.makeText(this,"Could not start Responsive/Fold trace: "+e.getClass().getSimpleName(),
          android.widget.Toast.LENGTH_LONG).show();
    }
  }

  private void infinityExportResponsiveTrace()
  {
    try
    {
      mInfinityResponsiveTraceExportFile=InfinityResponsiveTrace.stopAndBuildArchive(this);
      Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
      intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType("application/zip");
      intent.putExtra(Intent.EXTRA_TITLE,mInfinityResponsiveTraceExportFile.getName());
      startActivityForResult(intent,INFINITY_RESPONSIVE_TRACE_EXPORT_RESULT_CODE);
    }
    catch(Exception e)
    {
      mInfinityResponsiveTraceExportFile=null;
      android.widget.Toast.makeText(this,"Could not finish Responsive/Fold trace: "+e.getClass().getSimpleName(),
          android.widget.Toast.LENGTH_LONG).show();
    }
  }
'''
 s=once(s,oldreport,newreport,'trace health methods')
 return s

def apply(root,out):
 src=root/'shell-kodi'
 for p,expected in PRE.items():
  got=sha(src/p)
  if got!=expected:raise RuntimeError(f'Not exact 2103284 Android shell: {p} {got}')
 if (src/TRACE).exists():raise RuntimeError('Unexpected existing responsive trace class')
 (src/TRACE).write_bytes((Path(__file__).parent/'InfinityResponsiveTrace.java.in').read_bytes())
 (src/HEALTH).write_text(patch_health((src/HEALTH).read_text()))
 (src/MAIN).write_text(patch_main((src/MAIN).read_text()))
 (src/SPLASH).write_text(patch_splash((src/SPLASH).read_text()))
 install=(src/INSTALL).read_text()
 install=once(install,'                  src/InfinityExitDiagnostics.java\n',
              '                  src/InfinityExitDiagnostics.java\n                  src/InfinityResponsiveTrace.java\n','register trace class')
 (src/INSTALL).write_text(install)
 gradle=(src/GRADLE).read_text()
 gradle=once(gradle,'versionCode 2103284',f'versionCode {VC}','version code')
 gradle=once(gradle,'versionName "1.0.9-Ambient-Surface-Repair-RC1"',f'versionName "{REL}"','version name')
 (src/GRADLE).write_text(gradle)

 # Repoint the proven Android-only packager from 2103284 to exact signed 2103285 parent.
 p=root/'scripts/infinity_background_resume.py';text=p.read_text()
 for a,b in [
  ("VERSION_CODE = 2103284",f"VERSION_CODE = {VC}"),
  ("RELEASE = '1.0.9-Ambient-Surface-Repair-RC1'",f"RELEASE = '{REL}'"),
  ("BASE_COMMIT = 'ec28a8574ecf8d7fccb3713133661c1e8c2246cb'",f"BASE_COMMIT = '{BASE_COMMIT}'"),
  ("BASE_APK_SHA256 = '2de48f4a269df9196e341c1083608a436fdce1e2d63d17fbb2b80d9c525f63bf'",f"BASE_APK_SHA256 = '{BASE_APK}'"),
  ("BASE_ENGINE_SHA256 = 'c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'",f"BASE_ENGINE_SHA256 = '{BASE_ENGINE}'")
 ]:text=once(text,a,b,'packager metadata')
 p.write_text(text)
 p=root/'scripts/package_background_resume.py';text=p.read_text()
 text=text.replace('Infinity-2103284-Ambient-Surface-Repair-RC1-unsigned.apk','Infinity-2103288-Evidence-First-Health-RC1-unsigned.apk')
 text=text.replace('Infinity-2103284-Ambient-Surface-Repair-RC1.apk','Infinity-2103288-Evidence-First-Health-RC1.apk')
 text=text.replace("'base_run':36829442559","'base_run':36933314038")
 text=text.replace("ROOT/'repairs/infinity-ambient-surface-2103284/DEVICE-TEST.txt'","ROOT/'repairs/evidence-health-2103288/DEVICE-TEST.md'")
 p.write_text(text)

 receipt=root/'engine/background-resume-source.json';r=json.loads(receipt.read_text())
 r.update(base_source_commit=BASE_COMMIT,base_apk_sha256=BASE_APK,native_engine_sha256=BASE_ENGINE,
          version_code=VC,release=REL,candidate_locked=False,physical_device_verified=False,
          evidence_first_health=True,responsive_trace_user_controlled=True,network_upload=False,
          automatic_repair=False,native_source_modified=False,skin_modified=False)
 for name in (MAIN,SPLASH,HEALTH,INSTALL,GRADLE,TRACE):
  r['files'].setdefault(str(name),{})['after']=sha(src/name)
 receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 out.mkdir(parents=True,exist_ok=True)
 (out/'source-proof.json').write_text(json.dumps({
  'schema':1,'base_apk_sha256':BASE_APK,'native_engine_sha256':BASE_ENGINE,
  'source_parent':BASE_COMMIT,'version_code':VC,'version_name':REL,
  'android_diagnostics_only':True,'native_engine_recompiled':False,'skin_modified':False,
  'network_upload':False,'automatic_repair':False,'device_verified':False
 },indent=2,sort_keys=True)+'\n')
 verify(root)

def verify(root):
 src=root/'shell-kodi';m=(src/MAIN).read_text();s=(src/SPLASH).read_text();h=(src/HEALTH).read_text();i=(src/INSTALL).read_text()
 required=[
  'InfinityResponsiveTrace.capture(this, event, mMainView',
  'infinityTraceWindowSettled("main.configuration.settled")',
  'infinityTraceWindow("bridge.publish")',
  'Start Responsive/Fold Trace','Stop & export Responsive/Fold Trace',
  'InfinityResponsiveTrace.stopAndBuildArchive(this)',
  'INFINITY_RESPONSIVE_TRACE_EXPORT_RESULT_CODE = 8952',
  'rows.length<1||rows.length>8||rows.length!=handlers.length',
  'src/InfinityResponsiveTrace.java'
 ]
 blob='\n'.join((m,s,h,i))
 for token in required:
  if token not in blob:raise RuntimeError('Missing Health trace contract: '+token)
 trace=(src/TRACE).read_text()
 for token in ('getCurrentWindowMetrics().getBounds()','_','requested=','committed=',
               'Loading skin file:','Infinity geometry committed:','KODI GEOMETRY UPDATED; SKIN PROFILE RELOAD NOT OBSERVED',
               'network_upload=false','automatic_repair=false'):
  if token not in trace:raise RuntimeError('Missing trace evidence contract: '+token)
 if 'startActivity(' in trace or 'http://' in trace or 'https://' in trace:
  raise RuntimeError('Trace helper must not launch/network')
 print('PASS: Evidence-First Health trace source verified; no Kodi/native/skin repair behavior changed')

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['apply','verify']);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.mode=='apply':apply(a.root.resolve(),a.out.resolve())
 else:verify(a.root.resolve())
if __name__=='__main__':main()
