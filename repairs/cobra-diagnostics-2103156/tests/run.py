#!/usr/bin/env python3
"""Executable production archive/XML tests and strict source integration checks; not Android/device acceptance."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));import apply

def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 before=a.baseline.read_text();after,receipt=apply.patch_activity(before);(out/'InfinityLiveActivity.java.in').write_text(after)
 feature=(ROOT.parents[1]/'patches/infinity-cobra-v2/InfinityCobraFeatureRuntime.java.in').read_text();repaired=apply.patch_feature(feature)
 (out/'InfinityCobraFeatureRuntime.java.in').write_text(repaired)
 checks=[]
 def check(v,label):
  if not v:raise AssertionError(label)
  checks.append(label);print('PASS:',label)
 for value in (before+'\n',before.replace('REQUEST_LOCAL_MEDIA = 4172','REQUEST_LOCAL_MEDIA = 4174')):
  try:apply.patch_activity(value)
  except ValueError:check(True,'Unknown/modified Activity rejected')
  else:raise AssertionError('Accepted unknown source')
 check('"candidate-2"' not in repaired,'Installed version replaces hard-coded candidate name')
 check('if (target.exists() && !target.delete())' not in repaired,'Delete-before-replace snapshot bug removed')
 check('mFeatures.healthSnapshot()' not in after,'Health action no longer presents old snapshot as live')
 check('parser.getAttributeValue(null,"version")' in after,'UI identity comes from addon element')
 check(len(receipt['protected_methods'])>=370,'Untargeted Activity methods remain byte-identical')
 check(after.count('REQUEST_COBRA_DIAGNOSTICS = 4174')==1,'Unique result request code')
 check('if(!requested)return;' in after,'Unsolicited picker result ignored')
 check('if(resultCode!=RESULT_OK)' in after,'Picker cancellation does not export')
 check('data==null||data.getData()==null' in after,'Missing URI handled')
 check('state.putBoolean("cobra_diagnostics_picker"' in after and 'state.getBoolean("cobra_diagnostics_picker"' in after,'Picker state saved/restored for recreation')
 check('snapshot_kind","live_activity_observation' in after,'Fresh snapshot marked honestly')
 check('crash_history' in after,'Snapshot does not claim absence of crashes')
 runtime=(ROOT/'InfinityCobraDiagnostics.java.in').read_text()
 check('Intent.ACTION_CREATE_DOCUMENT' in runtime and '.setType("application/zip")' in runtime,'Save-as picker configured for ZIP')
 check('setDefaultUncaughtExceptionHandler' not in runtime and 'System.loadLibrary' not in runtime,'Native and uncaught handlers untouched')
 check('new Thread(' in runtime and 'getHistoricalProcessExitReasons(app.getPackageName(),0,8)' in runtime,'Bounded own-app exit query runs off UI')
 check('compareAndSet(false,true)' in runtime and 'EXPORTING.set(false)' in runtime,'Single export and release on completion/failure')
 check('last-error.json' in runtime and '"error".equals(category)' in runtime,'Later lifecycle success does not erase last error')
 check('native_binary_omitted_for_privacy' in runtime,'Raw native memory traces not silently exported')
 check('openOutputStream(destination,"w")' in runtime and 'if(out==null)' in runtime,'Unavailable document output stream handled')
 check('zip.delete()' in runtime,'App-private staging cleaned on success/failure')
 check('deleteDocument(app.getContentResolver(),destination)' in runtime,'Partial created document cleanup attempted')
 src=out/'java';src.mkdir(exist_ok=True)
 (src/'CobraDiagnosticArchive.java').write_text((ROOT/'CobraDiagnosticArchive.java.in').read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi'))
 shutil.copy2(ROOT/'tests/ArchiveTest.java',src)
 subprocess.run(['javac','--release','8','-d',str(out/'classes'),str(src/'CobraDiagnosticArchive.java'),str(src/'ArchiveTest.java')],check=True)
 r=subprocess.run(['java','-cp',str(out/'classes'),'com.projectinfinity.kodi.ArchiveTest'],capture_output=True,text=True,check=True);print(r.stdout);(out/'archive-tests.txt').write_text(r.stdout)
 # Execute the real new UI-version method with the inherited StAX pull-parser adapter.
 x,y=apply.span(after,'activeCobraUiLabel');method=after[x:y]
 repo=ROOT.parents[1];sys.path.insert(0,str(repo/'tests/cobra_2103153'));import test_refinement as inherited
 xmlsrc=out/'xml';xmlsrc.mkdir(exist_ok=True)
 files={'org/xmlpull/v1/XmlPullParserException.java':'package org.xmlpull.v1; public class XmlPullParserException extends Exception {public XmlPullParserException(String m){super(m);}}','org/xmlpull/v1/XmlPullParser.java':inherited.XML_INTERFACE,'android/util/Xml.java':inherited.XML_ADAPTER}
 for name,text in files.items():path=xmlsrc/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
 java='''import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import org.xmlpull.v1.*;import android.util.Xml;
public class UiVersionTest {File external;File getExternalFilesDir(String n){return external;}
'''+method+'''
public static void main(String[] args)throws Exception{UiVersionTest t=new UiVersionTest();t.external=Files.createTempDirectory("cobra-ui-version-").toFile();File f=new File(t.external,".kodi/addons/script.infinity.cobra.theme/addon.xml");f.getParentFile().mkdirs();
String[] cases={"<?xml version=\\"1.0\\"?><addon id=\\"script.infinity.cobra.theme\\" version=\\"1.3.9\\"/>","<addon version='1.3.9' id='script.infinity.cobra.theme'/>","<?xml version='1.0'?><addon id='wrong' version='1.3.9'/>","<broken>"};
for(int i=0;i<cases.length;i++){Files.write(f.toPath(),cases[i].getBytes(StandardCharsets.UTF_8));String label=t.activeCobraUiLabel();if(i<2&&!label.contains("1.3.9"))throw new AssertionError(label);if(i>=2&&!label.contains("UNAVAILABLE"))throw new AssertionError(label);}
f.delete();if(!t.activeCobraUiLabel().contains("APK DEFAULT"))throw new AssertionError("missing file");t.external=null;if(!t.activeCobraUiLabel().contains("APK DEFAULT"))throw new AssertionError("unmounted");System.out.println("PASS: 6 production XML version scenarios, including XML declaration 1.0 regression");}}
'''
 (xmlsrc/'UiVersionTest.java').write_text(java)
 subprocess.run(['javac','-d',str(out/'xmlclasses')]+[str(p) for p in xmlsrc.rglob('*.java')],check=True)
 r2=subprocess.run(['java','-cp',str(out/'xmlclasses'),'UiVersionTest'],capture_output=True,text=True,check=True);print(r2.stdout)
 report={'baseline':apply.sha(before),'patched':apply.sha(after),'integration_checks':checks,'archive_output':r.stdout,'ui_version_output':r2.stdout,'android_saf_device_tested':False,'protected_activity_methods':len(receipt['protected_methods'])}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
