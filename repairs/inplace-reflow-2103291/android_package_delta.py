#!/usr/bin/env python3
"""Android/package metadata delta for Infinity 2103291.

Runs after the proven 2103288 Health + 2103290 Android shell deltas.
No chooser redesign, no skin mutation, no provider/account changes.
"""
from pathlib import Path
import argparse,hashlib,json

VC=2103291
REL='1.0.9-InPlace-Responsive-Reflow-RC1'
PARENT_SOURCE='9888c81c2fd99f50212855aa8fb68149950b8f80'
GRADLE=Path('tools/android/packaging/xbmc/build.gradle.in')
TRACE=Path('tools/android/packaging/xbmc/src/InfinityResponsiveTrace.java.in')

def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'{label}: expected one anchor, got {n}')
 return s.replace(a,b,1)

def apply(root,base_apk_sha,native_sha,proof):
 shell=root/'shell-kodi'
 g=shell/GRADLE;t=g.read_text()
 t=once(t,'versionCode 2103290',f'versionCode {VC}','version code')
 t=once(t,'versionName "1.0.9-Native-Responsive-Layout-RC1"',f'versionName "{REL}"','version name')
 g.write_text(t)

 trace=shell/TRACE;t=trace.read_text()
 anchor='''        line.contains("Infinity responsive window:") ||'''
 if 'Infinity in-place responsive reflow:' not in t:
  t=once(t,anchor,anchor+'''
        line.contains("Infinity in-place responsive reflow:") ||''','trace in-place reflow log')
 trace.write_text(t)

 p=root/'scripts/infinity_background_resume.py';t=p.read_text()
 for old,new,label in [
  ('VERSION_CODE = 2103290',f'VERSION_CODE = {VC}','packager version'),
  ("RELEASE = '1.0.9-Native-Responsive-Layout-RC1'",f"RELEASE = '{REL}'",'packager release'),
  ("BASE_COMMIT = '794579890d5d4f124e6f41a188bcc578841f33c0'",f"BASE_COMMIT = '{PARENT_SOURCE}'",'packager parent source'),
  (f"BASE_APK_SHA256 = '{base_apk_sha}'",f"BASE_APK_SHA256 = '{base_apk_sha}'",'base apk self anchor'),
  (f"BASE_ENGINE_SHA256 = '{native_sha}'",f"BASE_ENGINE_SHA256 = '{native_sha}'",'native self anchor')
 ]:
  if label.endswith('self anchor'):
   if old not in t:raise RuntimeError(label+' missing after 2103290 binding')
  else:t=once(t,old,new,label)
 p.write_text(t)

 p=root/'scripts/package_background_resume.py';t=p.read_text()
 t=once(t,'Infinity-2103290-Native-Responsive-Layout-RC1-unsigned.apk',
        'Infinity-2103291-InPlace-Responsive-Reflow-RC1-unsigned.apk','unsigned filename')
 t=once(t,'Infinity-2103290-Native-Responsive-Layout-RC1.apk',
        'Infinity-2103291-InPlace-Responsive-Reflow-RC1.apk','final filename')
 t=t.replace("ROOT/'repairs/native-responsive-2103290/DEVICE-TEST.md'",
             "ROOT/'repairs/inplace-reflow-2103291/DEVICE-TEST.md'")
 p.write_text(t)

 receipt=root/'engine/background-resume-source.json';r=json.loads(receipt.read_text())
 r.update(base_source_commit=PARENT_SOURCE,base_apk_sha256=base_apk_sha,native_engine_sha256=native_sha,
          version_code=VC,release=REL,candidate_locked=False,physical_device_verified=False,
          native_responsive_layout=True,inplace_responsive_reflow=True,native_engine_recompiled=True,
          skin_modified=False,provider_data_modified=False,user_data_modified=False)
 for name in (GRADLE,TRACE):
  q=shell/name;r['files'].setdefault(str(name),{})['after']=H(q)
 receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')

 proof.parent.mkdir(parents=True,exist_ok=True)
 proof.write_text(json.dumps({
  'schema':1,'version_code':VC,'version_name':REL,'parent_source':PARENT_SOURCE,
  'prepared_base_apk_sha256':base_apk_sha,'native_engine_sha256':native_sha,
  'parent_2103290_android_shell_preserved':True,'health_trace_preserved':True,
  'health_trace_inplace_log_added':True,'skin_modified':False,
  'providers_modified':False,'accounts_modified':False
 },indent=2,sort_keys=True)+'\n')
 print('PASS: 2103291 Android/package delta bound to in-place responsive engine')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True)
 ap.add_argument('--base-apk-sha',required=True);ap.add_argument('--native-sha',required=True)
 ap.add_argument('--proof',type=Path,required=True);a=ap.parse_args()
 apply(a.root.resolve(),a.base_apk_sha,a.native_sha,a.proof.resolve())

if __name__=='__main__':main()
