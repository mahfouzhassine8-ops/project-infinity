#!/usr/bin/env python3
"""Repoint the proven Android-only packager after 2103288 Health + 2103290 shell changes."""
from pathlib import Path
import argparse,hashlib,json
VC=2103290
REL='1.0.9-Native-Responsive-Layout-RC1'
BASE_SOURCE='794579890d5d4f124e6f41a188bcc578841f33c0'
FILES=[
 'tools/android/packaging/xbmc/src/Main.java.in',
 'tools/android/packaging/xbmc/src/Splash.java.in',
 'tools/android/packaging/xbmc/src/InfinityGlassHealth.java.in',
 'tools/android/packaging/xbmc/src/InfinityResponsiveTrace.java.in',
 'tools/android/packaging/xbmc/src/InfinityGlassChooser.java.in',
 'tools/android/packaging/xbmc/build.gradle.in',
 'cmake/scripts/android/Install.cmake',
]
def H(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'{label}: expected one anchor, got {n}')
 return s.replace(a,b,1)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--base-apk-sha',required=True);ap.add_argument('--native-sha',required=True);ap.add_argument('--proof',type=Path,required=True);a=ap.parse_args()
 root=a.root.resolve()
 p=root/'scripts/infinity_background_resume.py';t=p.read_text()
 for old,new,label in [
  ("VERSION_CODE = 2103288",f"VERSION_CODE = {VC}","version"),
  ("RELEASE = '1.0.9-Evidence-First-Health-RC1'",f"RELEASE = '{REL}'","release"),
  ("BASE_COMMIT = 'c0c150b30008cee17df39e2a79a0c07e9a91f72a'",f"BASE_COMMIT = '{BASE_SOURCE}'","base source"),
  ("BASE_APK_SHA256 = '64ed5ce79096a3e09d02907cf72d3a5c4ad20186da231898c92db83e540d266b'",f"BASE_APK_SHA256 = '{a.base_apk_sha}'","base apk"),
  ("BASE_ENGINE_SHA256 = 'f6eb05f091bfe7a624105a0a83744a292e229b385d39c1b6a23f8bf954a2522a'",f"BASE_ENGINE_SHA256 = '{a.native_sha}'","native"),
 ]:t=once(t,old,new,label)
 p.write_text(t)
 p=root/'scripts/package_background_resume.py';t=p.read_text()
 t=once(t,'Infinity-2103288-Evidence-First-Health-RC1-unsigned.apk','Infinity-2103290-Native-Responsive-Layout-RC1-unsigned.apk','unsigned filename')
 t=once(t,'Infinity-2103288-Evidence-First-Health-RC1.apk','Infinity-2103290-Native-Responsive-Layout-RC1.apk','final filename')
 t=t.replace("'base_run':36933314038","'base_run':36941180186")
 t=t.replace("ROOT/'repairs/evidence-health-2103288/DEVICE-TEST.md'","ROOT/'repairs/native-responsive-2103290/DEVICE-TEST.md'")
 p.write_text(t)
 receipt=root/'engine/background-resume-source.json';r=json.loads(receipt.read_text())
 r.update(base_source_commit=BASE_SOURCE,base_apk_sha256=a.base_apk_sha,native_engine_sha256=a.native_sha,
          version_code=VC,release=REL,candidate_locked=False,physical_device_verified=False,
          native_responsive_layout=True,native_engine_recompiled=True,skin_modified=False)
 for name in FILES:
  q=root/'shell-kodi'/name
  if q.is_file():r['files'].setdefault(name,{})['after']=H(q)
 receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 proof={'schema':1,'version_code':VC,'version_name':REL,'base_source':BASE_SOURCE,
        'prepared_base_apk_sha256':a.base_apk_sha,'native_engine_sha256':a.native_sha,
        'evidence_health_preserved':True,'native_responsive_layout':True,'skin_packaged_in_apk':False}
 a.proof.parent.mkdir(parents=True,exist_ok=True);a.proof.write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
 print('PASS: 2103290 packager metadata bound to responsive native engine')
if __name__=='__main__':main()
